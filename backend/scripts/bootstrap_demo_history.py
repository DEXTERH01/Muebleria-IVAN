"""Load a deterministic, clearly labelled operating history into Supabase."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import hypot
from random import Random
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.algorithms.astar import optimize_route
from app.algorithms.hill_climbing import (
    ProductionTask,
    ProductionWeights,
    optimize_production_sequence,
)
from app.core.config import Settings

SEED = 20261121
TAG = "DEMO-2026"
START_AT = datetime(2026, 1, 5, 14, 0, tzinfo=UTC)
REFERENCE_AT = datetime(2026, 11, 21, 18, 0, tzinfo=UTC)
CUSTOMER_COUNT = 48
QUOTE_COUNT = 120
NAMESPACE = uuid5(NAMESPACE_URL, "muebleria-ivan/demo-history/v1")

FIRST_NAMES = (
    "Ana",
    "Luis",
    "María",
    "Carlos",
    "Rosa",
    "Jorge",
    "Lucía",
    "Miguel",
    "Carmen",
    "Diego",
    "Patricia",
    "José",
    "Elena",
    "Renato",
    "Sofía",
    "Marco",
    "Claudia",
    "Fernando",
    "Valeria",
    "Ricardo",
    "Diana",
    "Alonso",
    "Mónica",
    "Andrés",
)
LAST_NAMES = (
    "Torres",
    "Ramos",
    "Quispe",
    "Flores",
    "Vargas",
    "Mendoza",
    "Castillo",
    "Rojas",
    "Gutiérrez",
    "Salazar",
    "Paredes",
    "Chávez",
    "Navarro",
    "Medina",
    "Soto",
    "Campos",
    "Córdova",
    "Reyes",
    "Aguilar",
    "Espinoza",
    "Vega",
    "Herrera",
    "Cruz",
    "Palacios",
)
DISTRICTS = (
    ("Los Olivos", -11.9680, -77.0740),
    ("San Martín de Porres", -12.0300, -77.0570),
    ("Comas", -11.9340, -77.0450),
    ("Independencia", -11.9920, -77.0540),
    ("Puente Piedra", -11.8650, -77.0760),
    ("Cercado de Lima", -12.0464, -77.0428),
    ("Breña", -12.0560, -77.0510),
    ("Pueblo Libre", -12.0760, -77.0630),
    ("San Miguel", -12.0780, -77.0910),
    ("Jesús María", -12.0750, -77.0490),
    ("San Borja", -12.1070, -77.0000),
    ("Santiago de Surco", -12.1450, -77.0080),
    ("Ate", -12.0260, -76.9210),
    ("La Molina", -12.0820, -76.9280),
    ("Callao", -12.0610, -77.1180),
)
ORDER_STAGES = (
    "confirmed",
    "materials_pending",
    "cutting",
    "assembly",
    "finishing",
    "ready",
    "delivered",
    "installed",
)
PRODUCTION_STAGES = ("materials_pending", "cutting", "assembly", "finishing")


def stable_id(kind: str, value: object) -> UUID:
    return uuid5(NAMESPACE, f"{kind}:{value}")


def rounded_minor(value: float) -> int:
    return max(100, int(round(value / 100)) * 100)


def select_order_status(age_days: int, roll: float) -> str:
    if age_days > 120:
        if roll < 0.78:
            return "installed"
        if roll < 0.90:
            return "delivered"
        if roll < 0.96:
            return "cancelled"
        return "ready"
    if age_days > 60:
        if roll < 0.52:
            return "installed"
        if roll < 0.67:
            return "delivered"
        if roll < 0.78:
            return "ready"
        if roll < 0.88:
            return "finishing"
        if roll < 0.95:
            return "assembly"
        return "cancelled"
    if age_days > 30:
        return ("materials_pending", "cutting", "assembly", "finishing", "ready")[
            min(4, int(roll * 5))
        ]
    max_index = max(0, min(5, age_days // 4))
    return ORDER_STAGES[int(roll * (max_index + 1))]


def upsert_rows(connection, table: Table, rows: list[dict], *, immutable: bool = False) -> int:
    if not rows:
        return 0
    for offset in range(0, len(rows), 300):
        chunk = rows[offset : offset + 300]
        statement = pg_insert(table).values(chunk)
        if immutable:
            statement = statement.on_conflict_do_nothing(index_elements=[table.c.id])
        else:
            mutable = {
                key: statement.excluded[key] for key in chunk[0] if key != "id" and key in table.c
            }
            statement = statement.on_conflict_do_update(index_elements=[table.c.id], set_=mutable)
        connection.execute(statement)
    return len(rows)


def load_reference_data(connection) -> dict[str, object]:
    products = list(
        connection.execute(
            text(
                """
                select id, slug::text, name, category, base_price_minor,
                       min_production_days, max_production_days,
                       min_width_mm, max_width_mm, min_height_mm, max_height_mm,
                       min_depth_mm, max_depth_mm
                from app.products where active order by slug
                """
            )
        ).mappings()
    )
    materials = list(
        connection.execute(
            text("select id, code::text, name from app.materials where active order by code")
        ).mappings()
    )
    finishes = list(
        connection.execute(
            text("select id, code::text, name from app.finishes where active order by code")
        ).mappings()
    )
    accessories = list(
        connection.execute(
            text("select id, code::text, name from app.accessories where active order by code")
        ).mappings()
    )
    users = {
        row["email"]: row["user_id"]
        for row in connection.execute(
            text(
                """
                select lower(u.email) as email, p.user_id
                from auth.users u join app.profiles p on p.user_id = u.id
                where lower(u.email) in (
                  'admin.demo@example.com', 'operador.demo@example.com',
                  'cliente.ana.demo@example.com', 'cliente.luis.demo@example.com'
                )
                """
            )
        ).mappings()
    }
    if not products or not materials or not finishes:
        raise SystemExit("El catálogo publicado no contiene productos, materiales o acabados.")
    required_users = {
        "admin.demo@example.com",
        "operador.demo@example.com",
        "cliente.ana.demo@example.com",
        "cliente.luis.demo@example.com",
    }
    if set(users) != required_users:
        raise SystemExit("Primero ejecuta bootstrap_demo_accounts.py para crear las cuentas demo.")
    return {
        "products": products,
        "materials": materials,
        "finishes": finishes,
        "accessories": accessories,
        "users": users,
    }


def build_demo_rows(reference: dict[str, object]) -> dict[str, list[dict]]:
    rng = Random(SEED)
    rows: dict[str, list[dict]] = defaultdict(list)
    customers: list[dict] = []
    locations: list[dict] = []
    users = reference["users"]
    products = reference["products"]
    materials = reference["materials"]
    finishes = reference["finishes"]
    accessories = reference["accessories"]
    admin_id = users["admin.demo@example.com"]
    operator_id = users["operador.demo@example.com"]

    for index in range(1, CUSTOMER_COUNT + 1):
        customer_id = stable_id("customer", index)
        district, latitude, longitude = DISTRICTS[(index * 7) % len(DISTRICTS)]
        if index == 1:
            full_name = "Ana Cliente Demo"
            email = "cliente.ana.demo@example.com"
            profile_user_id = users[email]
        elif index == 2:
            full_name = "Luis Cliente Demo"
            email = "cliente.luis.demo@example.com"
            profile_user_id = users[email]
        else:
            first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
            last_name = LAST_NAMES[(index * 5) % len(LAST_NAMES)]
            full_name = f"{first_name} {last_name}"
            email = f"cliente.demo.{index:03d}@muebleria-ivan.test"
            profile_user_id = None
        created_at = START_AT - timedelta(days=30 + index * 2)
        customer = {
            "id": customer_id,
            "profile_user_id": profile_user_id,
            "full_name": full_name,
            "email": email,
            "phone": f"+51 900 {index:03d} {100 + index:03d}",
            "document_number": f"DEM{index:05d}",
            "address": f"Av. Demostración {200 + index}, {district}",
            "district": district,
            "notes": f"[{TAG}] Cliente ficticio para demostración académica.",
            "created_at": created_at,
            "updated_at": REFERENCE_AT,
        }
        location = {
            "id": stable_id("location", index),
            "customer_id": customer_id,
            "label": "Domicilio principal",
            "address": customer["address"],
            "district": district,
            "reference": f"Referencia ficticia {index:03d} — {TAG}",
            "latitude": Decimal(str(latitude + ((index % 5) - 2) * 0.0012)),
            "longitude": Decimal(str(longitude + ((index % 7) - 3) * 0.0011)),
            "created_at": created_at,
            "updated_at": REFERENCE_AT,
        }
        customers.append(customer)
        locations.append(location)
    rows["customers"] = customers
    rows["delivery_locations"] = locations

    location_by_customer = {location["customer_id"]: location for location in locations}
    orders_by_month: defaultdict[int, list[dict]] = defaultdict(list)
    history_days = (REFERENCE_AT - START_AT).days

    for index in range(1, QUOTE_COUNT + 1):
        created_at = START_AT + timedelta(
            days=(index - 1) * history_days / (QUOTE_COUNT - 1),
            hours=(index * 7) % 13,
        )
        if index % 9 == 0:
            customer = customers[0]
        elif index % 13 == 0:
            customer = customers[1]
        else:
            customer = customers[2 + rng.randrange(CUSTOMER_COUNT - 2)]
        customer_id = customer["id"]
        product = products[(index * 11 + rng.randrange(len(products))) % len(products)]
        material = materials[(index + rng.randrange(len(materials))) % len(materials)]
        finish = finishes[(index * 3 + rng.randrange(len(finishes))) % len(finishes)]
        width = rng.randint(product["min_width_mm"], product["max_width_mm"])
        height = rng.randint(product["min_height_mm"], product["max_height_mm"])
        depth = rng.randint(product["min_depth_mm"], product["max_depth_mm"])
        width = max(product["min_width_mm"], min(product["max_width_mm"], round(width / 10) * 10))
        height = max(
            product["min_height_mm"], min(product["max_height_mm"], round(height / 10) * 10)
        )
        depth = max(product["min_depth_mm"], min(product["max_depth_mm"], round(depth / 10) * 10))
        quantity = 2 if index % 11 == 0 else 1
        accessory_count = min(len(accessories), (index * 7) % 3)
        selected_accessories = [
            {
                "id": str(accessory["id"]),
                "code": accessory["code"],
                "name": accessory["name"],
            }
            for accessory in accessories[:accessory_count]
        ]
        size_factor = (
            0.68
            + 0.26 * width / product["max_width_mm"]
            + 0.20 * height / product["max_height_mm"]
            + 0.12 * depth / product["max_depth_mm"]
        )
        line_total = rounded_minor(
            product["base_price_minor"] * size_factor * quantity + accessory_count * 6_500
        )
        adjustments = 0
        if index % 6 == 0:
            adjustments += 12_000
        if index % 17 == 0:
            adjustments -= rounded_minor(line_total * 0.05)
        total = line_total + adjustments
        age_days = (REFERENCE_AT - created_at).days
        status_roll = rng.random()
        if age_days < 32:
            if status_roll < 0.52:
                quote_status = "converted"
            elif status_roll < 0.64:
                quote_status = "approved"
            elif status_roll < 0.78:
                quote_status = "reviewing"
            elif status_roll < 0.94:
                quote_status = "submitted"
            else:
                quote_status = "rejected"
        elif status_roll < 0.70:
            quote_status = "converted"
        elif status_roll < 0.84:
            quote_status = "rejected"
        else:
            quote_status = "expired"

        quote_id = stable_id("quote", index)
        quote_item_id = stable_id("quote-item", index)
        owner_user_id = customer["profile_user_id"]
        rows["quotes"].append(
            {
                "id": quote_id,
                "code": f"COT-DEMO-2026-{index:04d}",
                "customer_id": customer_id,
                "owner_user_id": owner_user_id,
                "contact_name": customer["full_name"],
                "contact_email": customer["email"],
                "contact_phone": customer["phone"],
                "status": quote_status,
                "currency": "PEN",
                "subtotal_minor": line_total,
                "adjustments_minor": adjustments,
                "total_minor": total,
                "deposit_minor": total // 2,
                "expires_at": created_at + timedelta(days=7),
                "version": 2 if quote_status in {"approved", "rejected", "converted"} else 1,
                "created_at": created_at,
                "updated_at": created_at + timedelta(days=2),
            }
        )
        rows["quote_items"].append(
            {
                "id": quote_item_id,
                "quote_id": quote_id,
                "product_id": product["id"],
                "quantity": quantity,
                "width_mm": width,
                "height_mm": height,
                "depth_mm": depth,
                "material_id": material["id"],
                "finish_id": finish["id"],
                "accessories": selected_accessories,
                "configuration": {
                    "material": material["name"],
                    "finish": finish["name"],
                    "installationIncluded": index % 4 != 0,
                    "syntheticTag": TAG,
                },
                "product_name_snapshot": product["name"],
                "base_price_minor": product["base_price_minor"],
                "calculation_breakdown": {
                    "referenceBaseMinor": product["base_price_minor"],
                    "sizeFactor": round(size_factor, 4),
                    "accessoriesMinor": accessory_count * 6_500,
                    "adjustmentsMinor": adjustments,
                    "dataLabel": "Datos sintéticos",
                },
                "line_total_minor": line_total,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
        session_id = stable_id("anonymous-session", index)
        for event_position, (event_name, delta_hours) in enumerate(
            (("product_viewed", -26), ("quote_started", -3), ("quote_submitted", 0))
        ):
            rows["customer_events"].append(
                {
                    "id": stable_id("customer-event", f"quote-{index}-{event_position}"),
                    "event_name": event_name,
                    "customer_id": customer_id,
                    "anonymous_session_id": None,
                    "occurred_at": created_at + timedelta(hours=delta_hours),
                    "properties": {
                        "productSlug": product["slug"],
                        "category": product["category"],
                        "source": "demo_history",
                        "syntheticTag": TAG,
                    },
                    "created_at": created_at + timedelta(hours=delta_hours),
                }
            )
        if index % 5 == 0:
            rows["customer_events"].append(
                {
                    "id": stable_id("customer-event", f"anonymous-{index}"),
                    "event_name": "catalog_search",
                    "customer_id": None,
                    "anonymous_session_id": session_id,
                    "occurred_at": created_at - timedelta(days=2),
                    "properties": {
                        "query": product["category"],
                        "resultCount": 4 + index % 15,
                        "syntheticTag": TAG,
                    },
                    "created_at": created_at - timedelta(days=2),
                }
            )

        if quote_status != "converted":
            continue

        order_id = stable_id("order", index)
        order_created_at = created_at + timedelta(days=1 + index % 4)
        order_age_days = max(0, (REFERENCE_AT - order_created_at).days)
        target_status = select_order_status(order_age_days, rng.random())
        complexity = round(
            1.0
            + accessory_count * 0.35
            + quantity * 0.25
            + width / max(1, product["max_width_mm"]) * 1.4,
            3,
        )
        workshop_load = 4 + (index * 7) % 17
        promised_days = max(
            product["min_production_days"],
            min(
                product["max_production_days"] + 8, round(8 + complexity * 5 + workshop_load * 0.35)
            ),
        )
        delayed = index % 5 == 0 or (complexity > 2.7 and index % 3 == 0)
        actual_days = max(5, promised_days + (3 + index % 5 if delayed else -(index % 3)))
        promised_date = (order_created_at + timedelta(days=promised_days)).date()
        location = location_by_customer[customer_id]
        actor_id = operator_id if index % 4 else admin_id

        if target_status == "cancelled":
            status_sequence = ("confirmed", "cancelled")
        else:
            status_sequence = ORDER_STAGES[: ORDER_STAGES.index(target_status) + 1]
        status_times: dict[str, datetime] = {}
        for stage_index, stage in enumerate(status_sequence):
            if target_status in {"installed", "delivered"}:
                final_index = max(1, len(status_sequence) - 1)
                occurred_at = order_created_at + timedelta(
                    days=actual_days * stage_index / final_index
                )
            else:
                occurred_at = min(
                    REFERENCE_AT - timedelta(hours=2),
                    order_created_at + timedelta(days=stage_index * 3 + stage_index % 2),
                )
            status_times[stage] = occurred_at
            rows["order_status_events"].append(
                {
                    "id": stable_id("order-status-event", f"{index}-{stage_index}"),
                    "order_id": order_id,
                    "previous_status": status_sequence[stage_index - 1] if stage_index else None,
                    "new_status": stage,
                    "actor_user_id": actor_id,
                    "note": f"[{TAG}] Avance simulado: {stage}",
                    "occurred_at": occurred_at,
                }
            )
            if stage_index:
                rows["audit_logs"].append(
                    {
                        "id": stable_id("audit", f"status-{index}-{stage_index}"),
                        "actor_user_id": actor_id,
                        "action": "demo.order.status_changed",
                        "entity_type": "order",
                        "entity_id": order_id,
                        "old_values": {"status": status_sequence[stage_index - 1]},
                        "new_values": {"status": stage, "syntheticTag": TAG},
                        "request_id": stable_id("request", f"status-{index}-{stage_index}"),
                        "ip_hash": "demo.local.x",
                        "created_at": occurred_at,
                    }
                )

        if target_status in {"delivered", "installed"}:
            paid_minor = total
        elif target_status == "cancelled" or (target_status == "confirmed" and index % 2):
            paid_minor = 0
        elif target_status == "ready" and index % 3 == 0:
            paid_minor = total
        else:
            paid_minor = total // 2
        delivered_at = status_times.get("delivered")
        installed_at = status_times.get("installed")
        order = {
            "id": order_id,
            "code": f"PED-DEMO-2026-{index:04d}",
            "quote_id": quote_id,
            "customer_id": customer_id,
            "status": target_status,
            "currency": "PEN",
            "total_minor": total,
            "deposit_required_minor": total // 2,
            "paid_minor": paid_minor,
            "version": len(status_sequence),
            "promised_date": promised_date,
            "delivered_at": delivered_at,
            "installed_at": installed_at,
            "delivery_address_snapshot": {
                "label": location["label"],
                "address": location["address"],
                "district": location["district"],
                "reference": location["reference"],
                "syntheticTag": TAG,
            },
            "created_at": order_created_at,
            "updated_at": status_times[status_sequence[-1]],
        }
        rows["orders"].append(order)
        orders_by_month[order_created_at.month].append(
            {
                **order,
                "material": material["name"],
                "complexity": complexity,
                "estimated_hours": round(5.5 + complexity * 4.8, 2),
            }
        )
        rows["order_items"].append(
            {
                "id": stable_id("order-item", index),
                "order_id": order_id,
                "source_quote_item_id": quote_item_id,
                "product_id": product["id"],
                "product_name_snapshot": product["name"],
                "quantity": quantity,
                "width_mm": width,
                "height_mm": height,
                "depth_mm": depth,
                "configuration_snapshot": {
                    "material": material["name"],
                    "finish": finish["name"],
                    "accessories": selected_accessories,
                    "syntheticTag": TAG,
                },
                "unit_price_minor": line_total // quantity,
                "line_total_minor": line_total,
                "created_at": order_created_at,
            }
        )
        rows["audit_logs"].append(
            {
                "id": stable_id("audit", f"conversion-{index}"),
                "actor_user_id": admin_id,
                "action": "demo.quote.converted",
                "entity_type": "order",
                "entity_id": order_id,
                "old_values": {"quoteStatus": "approved"},
                "new_values": {"quoteStatus": "converted", "syntheticTag": TAG},
                "request_id": stable_id("request", f"conversion-{index}"),
                "ip_hash": "demo.local.x",
                "created_at": order_created_at,
            }
        )

        stage_factors = {
            "materials_pending": 0.16,
            "cutting": 0.23,
            "assembly": 0.34,
            "finishing": 0.27,
        }
        for stage_position, stage in enumerate(PRODUCTION_STAGES):
            planned_start = order_created_at + timedelta(days=1 + stage_position * 3)
            estimated_hours = round((6 + complexity * 7) * stage_factors[stage], 2)
            planned_end = planned_start + timedelta(hours=estimated_hours)
            reached = stage in status_times
            active_stage = target_status == stage
            actual_start = status_times.get(stage) if reached else None
            actual_hours = (
                round(estimated_hours * (1.08 if delayed else 0.94 + (index % 5) * 0.02), 2)
                if reached and not active_stage
                else None
            )
            actual_end = (
                actual_start + timedelta(hours=actual_hours)
                if actual_start is not None and actual_hours is not None
                else None
            )
            rows["production_jobs"].append(
                {
                    "id": stable_id("production-job", f"{index}-{stage}"),
                    "order_id": order_id,
                    "stage": stage,
                    "priority": 55 + (index * 13 + stage_position * 7) % 46,
                    "complexity": Decimal(str(complexity)),
                    "estimated_hours": Decimal(str(estimated_hours)),
                    "actual_hours": Decimal(str(actual_hours))
                    if actual_hours is not None
                    else None,
                    "planned_start_at": planned_start,
                    "planned_end_at": planned_end,
                    "actual_start_at": actual_start,
                    "actual_end_at": actual_end,
                    "created_at": order_created_at,
                    "updated_at": actual_end or REFERENCE_AT,
                }
            )

        if target_status in {"ready", "delivered", "installed"}:
            delivery_day = delivered_at or datetime.combine(
                promised_date, datetime.min.time(), tzinfo=UTC
            )
            rows["deliveries"].append(
                {
                    "id": stable_id("delivery", index),
                    "order_id": order_id,
                    "delivery_location_id": location["id"],
                    "window_start_at": delivery_day.replace(hour=14),
                    "window_end_at": delivery_day.replace(hour=18),
                    "sequence": 1 + index % 6,
                    "estimated_distance_m": 3_500 + (index * 1_379) % 28_000,
                    "status": "delivered" if delivered_at else "scheduled",
                    "created_at": order_created_at,
                    "updated_at": delivered_at or order_created_at,
                }
            )

        payment_amounts: list[int] = []
        if paid_minor:
            first_amount = min(total // 2, paid_minor)
            payment_amounts.append(first_amount)
            if paid_minor > first_amount:
                payment_amounts.append(paid_minor - first_amount)
        for payment_position, amount in enumerate(payment_amounts, 1):
            paid_at = (
                order_created_at + timedelta(days=1)
                if payment_position == 1
                else (delivered_at or status_times.get("ready") or REFERENCE_AT) - timedelta(days=1)
            )
            payment_id = stable_id("payment", f"{index}-{payment_position}")
            rows["payments"].append(
                {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount_minor": amount,
                    "currency": "PEN",
                    "method": ("bank_transfer", "cash", "card", "other")[
                        (index + payment_position) % 4
                    ],
                    "reference": f"{TAG}-PAGO-{index:04d}-{payment_position}",
                    "paid_at": paid_at,
                    "status": "recorded",
                    "actor_user_id": actor_id,
                    "voucher_asset_id": None,
                    "idempotency_key": f"{TAG.lower()}:{index}:{payment_position}",
                    "reverses_payment_id": None,
                    "created_at": paid_at,
                }
            )
            rows["audit_logs"].append(
                {
                    "id": stable_id("audit", f"payment-{index}-{payment_position}"),
                    "actor_user_id": actor_id,
                    "action": "demo.payment.recorded",
                    "entity_type": "payment",
                    "entity_id": payment_id,
                    "old_values": {"paidMinor": sum(payment_amounts[: payment_position - 1])},
                    "new_values": {"amountMinor": amount, "syntheticTag": TAG},
                    "request_id": stable_id("request", f"payment-{index}-{payment_position}"),
                    "ip_hash": "demo.local.x",
                    "created_at": paid_at,
                }
            )

    for month in range(1, 12):
        monthly_orders = orders_by_month.get(month, [])
        if len(monthly_orders) < 3:
            continue
        selected_orders = monthly_orders[: min(7, len(monthly_orders))]
        tasks = [
            ProductionTask(
                task_id=order["code"],
                material=order["material"],
                duration_hours=order["estimated_hours"],
                due_in_hours=max(
                    24.0, (order["promised_date"] - order["created_at"].date()).days * 24.0
                ),
                ready_in_hours=float((position * 5 + month) % 19),
            )
            for position, order in enumerate(selected_orders)
        ]
        hill_result = optimize_production_sequence(
            tasks,
            ProductionWeights(delay_days=10.0, material_changes=3.0, idle_hours=2.0),
            random_seed=SEED + month,
            restarts=5,
            max_iterations=100,
        )
        created_at = datetime(2026, month, 24, 15, 0, tzinfo=UTC)
        rows["optimization_runs"].append(
            {
                "id": stable_id("optimization", f"hill-{month}"),
                "algorithm": "hill_climbing",
                "input": {
                    "tasks": [asdict(task) for task in tasks],
                    "syntheticTag": TAG,
                },
                "baseline": {
                    "sequence": list(hill_result.initial_sequence),
                    "score": asdict(hill_result.initial_score),
                },
                "result": {
                    "sequence": list(hill_result.recommended_sequence),
                    "score": asdict(hill_result.final_score),
                    "iterations": hill_result.iterations,
                    "restarts": hill_result.restarts,
                },
                "improvement": Decimal(str(round(hill_result.improvement_percent, 5))),
                "random_seed": hill_result.random_seed,
                "duration_ms": max(0, round(hill_result.duration_ms)),
                "requested_by": operator_id,
                "accepted": month % 4 != 0,
                "created_at": created_at,
            }
        )

        selected_districts = []
        for order in selected_orders:
            district = order["delivery_address_snapshot"]["district"]
            if district not in selected_districts:
                selected_districts.append(district)
            if len(selected_districts) == 5:
                break
        if len(selected_districts) < 2:
            continue
        coordinate_by_district = {
            district: (latitude, longitude) for district, latitude, longitude in DISTRICTS
        }
        start = "Taller Los Olivos"
        coordinates = {start: (-11.9680, -77.0740)}
        coordinates.update(
            {district: coordinate_by_district[district] for district in selected_districts}
        )
        distances = {
            origin: {
                destination: round(
                    hypot(
                        coordinates[origin][0] - coordinates[destination][0],
                        coordinates[origin][1] - coordinates[destination][1],
                    )
                    * 111_000,
                    1,
                )
                for destination in coordinates
            }
            for origin in coordinates
        }
        route_result = optimize_route(start, selected_districts, distances)
        rows["optimization_runs"].append(
            {
                "id": stable_id("optimization", f"astar-{month}"),
                "algorithm": "astar",
                "input": {
                    "start": start,
                    "stops": selected_districts,
                    "distances": distances,
                    "syntheticTag": TAG,
                },
                "baseline": {
                    "route": list(route_result.initial_route),
                    "distance": route_result.initial_distance,
                },
                "result": {
                    "route": list(route_result.recommended_route),
                    "distance": route_result.total_distance,
                    "exploredNodes": route_result.explored_nodes,
                },
                "improvement": Decimal(str(round(route_result.improvement_percent, 5))),
                "random_seed": None,
                "duration_ms": max(0, round(route_result.duration_ms)),
                "requested_by": admin_id,
                "accepted": month % 5 != 0,
                "created_at": created_at + timedelta(hours=1),
            }
        )
    return rows


def main() -> int:
    settings = Settings()
    if not settings.database_url:
        raise SystemExit("MUEBLERIA_DATABASE_URL no está configurada.")
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    immutable_tables = {"order_items", "order_status_events", "payments", "audit_logs"}
    table_order = (
        "customers",
        "delivery_locations",
        "quotes",
        "quote_items",
        "orders",
        "order_items",
        "order_status_events",
        "production_jobs",
        "deliveries",
        "payments",
        "customer_events",
        "predictions",
        "optimization_runs",
        "audit_logs",
    )
    try:
        with engine.begin() as connection:
            reference = load_reference_data(connection)
            rows = build_demo_rows(reference)
            print("Historial generado; sincronizando tablas...", flush=True)
            metadata = MetaData()
            counts: dict[str, int] = {}
            for table_name in table_order:
                table = Table(table_name, metadata, schema="app", autoload_with=connection)
                counts[table_name] = upsert_rows(
                    connection,
                    table,
                    rows[table_name],
                    immutable=table_name in immutable_tables,
                )
                print(f"- {table_name}: {counts[table_name]}", flush=True)
    finally:
        engine.dispose()
    print(f"Historial sintético {TAG} sincronizado en Supabase (semilla {SEED}):")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
