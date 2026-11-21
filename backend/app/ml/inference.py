"""Load approved local artifacts and provide deterministic advisory inference."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

from app.ml.training import ORDER_FEATURES

BACKEND_DIR = Path(__file__).resolve().parents[2]
MANIFEST_PATH = BACKEND_DIR / "artifacts" / "ml" / "manifest.json"


@dataclass(frozen=True)
class InferenceResult:
    problem: str
    algorithm: str
    version: int
    output: dict[str, object]
    confidence: float | None
    fallback_used: bool
    data_label: str = "Datos de prueba"


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=3)
def _load_model(problem: str) -> tuple[dict[str, Any], object]:
    entry = next(model for model in _manifest()["models"] if model["problem"] == problem)
    path = BACKEND_DIR / entry["artifactPath"]
    if not path.is_file() or _hash(path) != entry["artifactHash"]:
        raise FileNotFoundError(f"Artefacto inválido para {problem}.")
    return entry, joblib.load(path)


def feature_row(features: dict[str, object]) -> list[object]:
    return [features[name] for name in ORDER_FEATURES]


def predict_production_days(features: dict[str, object]) -> InferenceResult:
    try:
        entry, model = _load_model("production_days")
        days = max(2.0, float(model.predict([feature_row(features)])[0]))
        rmse = float(entry["metrics"]["test"]["rmse"])
        output = {
            "estimatedDays": round(days, 1),
            "intervalMinDays": max(2.0, round(days - 1.96 * rmse, 1)),
            "intervalMaxDays": round(days + 1.96 * rmse, 1),
        }
        return InferenceResult(
            problem="production_days",
            algorithm=entry["algorithm"],
            version=entry["version"],
            output=output,
            confidence=0.95,
            fallback_used=False,
        )
    except (FileNotFoundError, KeyError, ValueError, StopIteration):
        days = max(
            2.0,
            3
            + float(features["complexity_score"]) * 1.5
            + float(features["item_count"]) * 1.5
            + float(features["workshop_load"]) * 0.15,
        )
        return InferenceResult(
            problem="production_days",
            algorithm="rule_fallback",
            version=1,
            output={
                "estimatedDays": round(days, 1),
                "intervalMinDays": max(2.0, round(days - 3, 1)),
                "intervalMaxDays": round(days + 3, 1),
            },
            confidence=None,
            fallback_used=True,
        )


def predict_delay_risk(features: dict[str, object]) -> InferenceResult:
    try:
        entry, model = _load_model("delay_risk")
        probability = float(model.predict_proba([feature_row(features)])[0][1])
        output = {"isDelayed": probability >= 0.5, "probability": round(probability, 5)}
        confidence = max(probability, 1 - probability)
        return InferenceResult(
            problem="delay_risk",
            algorithm=entry["algorithm"],
            version=entry["version"],
            output=output,
            confidence=round(confidence, 5),
            fallback_used=False,
        )
    except (FileNotFoundError, KeyError, ValueError, StopIteration):
        score = (
            -4.8
            + 0.38 * float(features["complexity_score"])
            + 0.08 * float(features["workshop_load"])
            + 0.12 * float(features["accessory_count"])
        )
        probability = 1 / (1 + math.exp(-score))
        return InferenceResult(
            problem="delay_risk",
            algorithm="rule_fallback",
            version=1,
            output={"isDelayed": probability >= 0.5, "probability": round(probability, 5)},
            confidence=None,
            fallback_used=True,
        )
