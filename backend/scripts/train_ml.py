"""Train and version every demonstration model outside web requests."""

from pathlib import Path

from app.ml.training import SEED, train_all

if __name__ == "__main__":
    backend_dir = Path(__file__).resolve().parents[1]
    dataset = backend_dir.parent / "data" / "synthetic" / "orders_v1.csv"
    artifacts = backend_dir / "artifacts" / "ml"
    result = train_all(dataset, artifacts, seed=SEED)
    for model in result["models"]:
        print(f"{model['problem']}: {model['algorithm']} v{model['version']}")
    print(f"Artefactos y métricas calculadas: {artifacts}")
