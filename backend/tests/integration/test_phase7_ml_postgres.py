"""Real Auth, PostgreSQL and advisory ML checks on disposable local Supabase.

Uses the same SUPABASE_TEST_* variables as the Phase 4 workflow. Optionally set
PHASE7_ML_REPORT to save measured timings, without credentials or user data.
"""

import json
import math
import os
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app
from app.ml import inference
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction

DATABASE_URL = os.getenv("SUPABASE_TEST_DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_TEST_URL")
PUBLISHABLE_KEY = os.getenv("SUPABASE_TEST_PUBLISHABLE_KEY")
pytestmark = pytest.mark.skipif(
    not all((DATABASE_URL, SUPABASE_URL, PUBLISHABLE_KEY)),
    reason="Set SUPABASE_TEST_* to run advisory ML against local Supabase",
)
ENDPOINTS = ("production-days", "delay-risk")


def _create_user(role):
    password = f"Local-{uuid4().hex}!aA1"
    with httpx.Client(base_url=SUPABASE_URL, timeout=20) as client:
        response = client.post(
            "/auth/v1/signup",
            headers={"apikey": PUBLISHABLE_KEY},
            json={"email": f"phase7-{uuid4().hex}@example.test", "password": password},
        )
    assert response.status_code == 200
    account = response.json()
    assert account.get("access_token"), "Local Auth must allow sign-up without confirmation"
    return account["user"]["id"], account["access_token"], role


@pytest.fixture(scope="module")
def local_ml():
    assert DATABASE_URL and SUPABASE_URL and PUBLISHABLE_KEY
    for url in (DATABASE_URL, SUPABASE_URL):
        assert urlparse(url).hostname in {"localhost", "127.0.0.1", "::1"}, (
            "This suite writes test data and requires disposable local Supabase"
        )
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    accounts = [_create_user(role) for role in ("operator", "customer")]
    manifest = json.loads(inference.MANIFEST_PATH.read_text(encoding="utf-8"))
    with Session(engine) as session:
        for user_id, _, role in accounts:
            session.execute(
                text("update app.profiles set role = :role where user_id = :id"),
                {"role": role, "id": user_id},
            )
        for entry in manifest["models"]:
            session.execute(
                update(ModelVersion)
                .where(ModelVersion.problem == entry["problem"], ModelVersion.status == "active")
                .values(status="retired")
            )
            model = session.scalar(
                select(ModelVersion).where(
                    ModelVersion.problem == entry["problem"],
                    ModelVersion.algorithm == entry["algorithm"],
                    ModelVersion.version == entry["version"],
                )
            )
            if model is None:
                model = ModelVersion(
                    problem=entry["problem"], algorithm=entry["algorithm"], version=entry["version"]
                )
                session.add(model)
            model.artifact_path = entry["artifactPath"]
            model.artifact_hash = entry["artifactHash"]
            model.parameters = entry["parameters"]
            model.metrics = {**entry["metrics"], "dataLabel": manifest["dataLabel"]}
            model.status = "active"
        session.commit()
    with engine.connect() as connection:
        order_id = connection.scalar(text("select id from app.orders order by created_at limit 1"))
    assert order_id, "Run Supabase migrations and seed first"
    payload = {
        "orderId": str(order_id),
        "widthMm": 1800,
        "heightMm": 2200,
        "depthMm": 550,
        "accessoryCount": 1,
        "itemCount": 1,
        "complexityScore": 3,
        "workshopLoad": 8,
        "quotedTotalMinor": 145000,
        "promisedDays": 15,
        "customerFrequency": 1,
        "category": "Dormitorio",
        "material": "Melamina",
        "district": "Miraflores",
    }
    settings = Settings(environment="test", database_url=DATABASE_URL, supabase_url=SUPABASE_URL)
    try:
        with TestClient(create_app(settings)) as client:
            yield (
                client,
                engine,
                payload,
                {role: {"Authorization": f"Bearer {token}"} for _, token, role in accounts},
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_inference_rejects_anonymous_and_customer(local_ml, endpoint):
    client, _, payload, headers = local_ml
    path = f"/api/v1/ml/{endpoint}"
    assert client.post(path, json=payload).status_code == 401
    assert client.post(path, json=payload, headers=headers["customer"]).status_code == 403


def _business_snapshot(engine):
    with engine.connect() as connection:
        return {
            table: connection.scalar(
                text(f"select jsonb_agg(to_jsonb(t) order by id) from app.{table} t")
            )
            for table in ("orders", "payments")
        }


def test_versioned_predictions_persist_without_changing_orders_or_payments(local_ml):
    client, engine, payload, headers = local_ml
    before = _business_snapshot(engine)
    report = {
        "measuredAt": datetime.now(UTC).isoformat(),
        "environment": "local Supabase + FastAPI TestClient",
        "method": "nearest rank; 30 sequential warm samples after first request",
        "dataLabel": "Datos de prueba",
        "endpoints": {},
    }
    for endpoint in ENDPOINTS:
        durations = []
        prediction_ids = []
        cold_ms = None
        for index in range(31):
            started = perf_counter()
            response = client.post(
                f"/api/v1/ml/{endpoint}", json=payload, headers=headers["operator"]
            )
            elapsed = (perf_counter() - started) * 1000
            assert response.status_code == 200, response.text
            data = response.json()["data"]
            assert data["advisory"] is True
            assert data["dataLabel"] == "Datos de prueba"
            assert data["fallbackUsed"] is False
            assert data["modelVersion"] == 1
            prediction_ids.append(data["predictionId"])
            if index == 0:
                cold_ms = elapsed
            else:
                durations.append(elapsed)
        with Session(engine) as session:
            for prediction_id in prediction_ids:
                record = session.get(Prediction, prediction_id)
                assert record is not None
                model = session.get(ModelVersion, record.model_version_id)
                assert model is not None and model.version == 1
                assert record.output["modelVersion"] == model.version
                assert record.output["fallbackUsed"] is False
        ordered = sorted(durations)
        report["endpoints"][endpoint] = {
            "samples": len(durations),
            "httpErrors": 0,
            "firstRequestMs": round(cold_ms, 3),
            "p50Ms": round(ordered[math.ceil(len(ordered) * 0.50) - 1], 3),
            "p95Ms": round(ordered[math.ceil(len(ordered) * 0.95) - 1], 3),
        }
    assert _business_snapshot(engine) == before
    report_path = os.getenv("PHASE7_ML_REPORT")
    if report_path:
        Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_missing_artifact_uses_persisted_advisory_fallback(local_ml, monkeypatch, endpoint):
    client, engine, payload, headers = local_ml

    def missing_artifact(_problem):
        raise FileNotFoundError("Missing local artifact for fallback check")

    before = _business_snapshot(engine)
    monkeypatch.setattr(inference, "_load_model", missing_artifact)
    response = client.post(f"/api/v1/ml/{endpoint}", json=payload, headers=headers["operator"])
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["advisory"] is True and data["fallbackUsed"] is True
    assert data["algorithm"] == "rule_fallback"
    with Session(engine) as session:
        record = session.get(Prediction, data["predictionId"])
        assert record is not None and record.output["fallbackUsed"] is True
    assert _business_snapshot(engine) == before
