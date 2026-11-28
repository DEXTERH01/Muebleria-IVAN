"""Generate the versioned synthetic dataset used by the ML pipeline."""

from pathlib import Path

from app.ml.dataset import SEED, write_dataset

if __name__ == "__main__":
    output = Path(__file__).resolve().parents[2] / "data" / "synthetic" / "orders_v1.csv"
    write_dataset(output, count=500, seed=SEED)
    print(f"Dataset de prueba generado: {output} (500 filas, semilla {SEED})")
