"""Synchronize trained model metadata with app.model_versions."""

import json
from pathlib import Path

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.model_version import ModelVersion

if __name__ == "__main__":
    backend_dir = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (backend_dir / "artifacts" / "ml" / "manifest.json").read_text(encoding="utf-8")
    )
    settings = Settings()
    if not settings.database_url:
        raise SystemExit("MUEBLERIA_DATABASE_URL no está configurada.")

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as session:
        for entry in manifest["models"]:
            session.execute(
                update(ModelVersion)
                .where(
                    ModelVersion.problem == entry["problem"],
                    ModelVersion.status == "active",
                )
                .values(status="retired")
            )
            model = session.scalar(
                select(ModelVersion).where(
                    ModelVersion.problem == entry["problem"],
                    ModelVersion.algorithm == entry["algorithm"],
                    ModelVersion.version == entry["version"],
                )
            )
            values = {
                "artifact_path": entry["artifactPath"],
                "artifact_hash": entry["artifactHash"],
                "parameters": {**entry["parameters"], "features": entry["features"]},
                "metrics": {**entry["metrics"], "dataLabel": manifest["dataLabel"]},
                "status": "active",
            }
            if model is None:
                session.add(
                    ModelVersion(
                        problem=entry["problem"],
                        algorithm=entry["algorithm"],
                        version=entry["version"],
                        **values,
                    )
                )
            else:
                for field, value in values.items():
                    setattr(model, field, value)
        session.commit()
    print(f"Modelos activos registrados: {len(manifest['models'])}")
