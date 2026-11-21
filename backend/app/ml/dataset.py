"""Reproducible synthetic orders used only to validate the ML pipeline."""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SEED = 2026
REFERENCE_DATE = date(2026, 11, 21)

CATEGORIES = ("armario", "cocina", "escritorio", "mesa", "repisa")
MATERIALS = ("melamina", "mdf", "madera")
DISTRICTS = ("Ate", "La Molina", "San Borja", "San Luis", "Santa Anita")

FIELDNAMES = (
    "order_id",
    "customer_id",
    "order_date",
    "category",
    "material",
    "district",
    "width_mm",
    "height_mm",
    "depth_mm",
    "accessory_count",
    "item_count",
    "complexity_score",
    "workshop_load",
    "quoted_total_minor",
    "promised_days",
    "customer_recency_days",
    "customer_frequency",
    "customer_total_spend_minor",
    "customer_avg_ticket_minor",
    "categories_bought",
    "production_days",
    "is_delayed",
)


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def generate_orders(count: int = 500, seed: int = SEED) -> list[dict[str, object]]:
    """Create anonymous orders with controlled, learnable relationships."""
    if count < 100:
        raise ValueError("El dataset debe contener al menos 100 pedidos.")

    rng = random.Random(seed)
    customer_count = max(80, count // 5)
    customer_weights = [rng.uniform(0.4, 2.2) for _ in range(customer_count)]
    material_days = {"melamina": 0.0, "mdf": 1.2, "madera": 2.5}
    category_days = {"repisa": 0.0, "mesa": 1.0, "escritorio": 1.6, "armario": 2.5, "cocina": 4.0}
    rows: list[dict[str, object]] = []

    for index in range(count):
        customer_number = rng.choices(range(customer_count), weights=customer_weights, k=1)[0]
        category = rng.choice(CATEGORIES)
        material = rng.choices(MATERIALS, weights=(0.52, 0.28, 0.20), k=1)[0]
        district = rng.choice(DISTRICTS)
        width_mm = rng.randrange(500, 3001, 50)
        height_mm = rng.randrange(400, 2501, 50)
        depth_mm = rng.randrange(300, 901, 25)
        accessory_count = rng.randint(0, 8)
        item_count = rng.randint(1, 4)
        complexity_score = rng.randint(1, 5)
        workshop_load = rng.randint(3, 28)
        volume_m3 = width_mm * height_mm * depth_mm / 1_000_000_000
        quoted_total_minor = round(
            35_000
            + volume_m3 * 42_000
            + complexity_score * 16_000
            + accessory_count * 4_500
            + item_count * 22_000
            + material_days[material] * 9_000
            + rng.gauss(0, 5_000)
        )
        promised_days = max(
            4,
            round(
                3.5
                + volume_m3 * 1.4
                + complexity_score * 1.1
                + item_count * 1.2
                + category_days[category] * 0.55
            ),
        )
        production_days = max(
            2,
            round(
                2.2
                + volume_m3 * 1.8
                + complexity_score * 1.45
                + accessory_count * 0.38
                + item_count * 1.5
                + workshop_load * 0.16
                + material_days[material]
                + category_days[category]
                + rng.gauss(0, 1.25)
            ),
        )
        delay_probability = _sigmoid(
            -4.8
            + 0.38 * complexity_score
            + 0.08 * workshop_load
            + 0.12 * accessory_count
            + 0.22 * material_days[material]
            + 0.12 * max(0, production_days - promised_days)
        )
        is_delayed = int(rng.random() < delay_probability)
        order_date = REFERENCE_DATE - timedelta(days=rng.randint(10, 720))
        rows.append(
            {
                "order_id": f"SYN-{index + 1:04d}",
                "customer_id": f"CUS-{customer_number + 1:03d}",
                "order_date": order_date.isoformat(),
                "category": category,
                "material": material,
                "district": district,
                "width_mm": width_mm,
                "height_mm": height_mm,
                "depth_mm": depth_mm,
                "accessory_count": accessory_count,
                "item_count": item_count,
                "complexity_score": complexity_score,
                "workshop_load": workshop_load,
                "quoted_total_minor": max(50_000, quoted_total_minor),
                "promised_days": promised_days,
                "production_days": production_days,
                "is_delayed": is_delayed,
            }
        )

    customer_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        customer_rows[str(row["customer_id"])].append(row)
    for purchases in customer_rows.values():
        latest = max(date.fromisoformat(str(row["order_date"])) for row in purchases)
        total = sum(int(row["quoted_total_minor"]) for row in purchases)
        categories = len({str(row["category"]) for row in purchases})
        summary = {
            "customer_recency_days": (REFERENCE_DATE - latest).days,
            "customer_frequency": len(purchases),
            "customer_total_spend_minor": total,
            "customer_avg_ticket_minor": round(total / len(purchases)),
            "categories_bought": categories,
        }
        for row in purchases:
            row.update(summary)
    return rows


def write_dataset(path: Path, count: int = 500, seed: int = SEED) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(generate_orders(count=count, seed=seed))
    return path
