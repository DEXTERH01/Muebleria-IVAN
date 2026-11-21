from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.catalog import PricingValidationError
from app.models.catalog import Accessory, Finish, Material, PricingRule, Product
from app.repositories.catalog import OptionRecord
from app.schemas.pricing import (
    EstimateItemRequest,
    PricingConditionRequest,
    PricingOperationRequest,
    PricingRuleCreateRequest,
    QuoteEstimateRequest,
)
from app.services.pricing import PricingService


def product() -> Product:
    return Product(
        id=uuid4(),
        slug="producto-prueba",
        name="Producto prueba",
        description="",
        category="Oficina",
        base_price_minor=100_000,
        active=True,
        min_production_days=7,
        max_production_days=10,
        min_width_mm=1000,
        max_width_mm=2000,
        min_height_mm=1000,
        max_height_mm=2000,
        min_depth_mm=500,
        max_depth_mm=1000,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def option(model, *, fixed: int = 0, percent: str = "0"):
    return model(
        id=uuid4(),
        code=f"OPT-{uuid4().hex[:6]}",
        name="Opción",
        description="",
        price_adjustment_minor=fixed,
        price_adjustment_percent=Decimal(percent),
        active=True,
        available=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class FakeCatalog:
    def __init__(self, value: Product) -> None:
        self.value = value

    def get_by_id(self, _product_id, *, active_only=True):
        return self.value


class FakePricing:
    def __init__(self, material, finish, accessories, rules) -> None:
        self.material_value = material
        self.finish_value = finish
        self.accessory_values = accessories
        self.rules = rules
        self.saved_rules = []
        self.deactivated_names = []
        self.commits = 0

    def material(self, _product_id, _option_id):
        return self.material_value

    def finish(self, _product_id, _option_id):
        return self.finish_value

    def accessories(self, _product_id, _option_ids):
        return self.accessory_values

    def active_rules(self, _at):
        return self.rules

    def all_rules(self):
        return [*self.rules, *self.saved_rules]

    def next_version(self, name):
        versions = [rule.version for rule in self.all_rules() if rule.name == name]
        return max(versions, default=0) + 1

    def deactivate_active_versions(self, name):
        self.deactivated_names.append(name)
        for rule in self.all_rules():
            if rule.name == name:
                rule.active = False

    def add(self, rule):
        self.saved_rules.append(rule)

    def commit(self):
        self.commits += 1

    def rollback(self):
        return None


def test_estimate_applies_dimensions_options_rules_and_deposit() -> None:
    item_product = product()
    material = OptionRecord(option(Material, fixed=10_000), True)
    finish = OptionRecord(option(Finish, percent="10"), True)
    accessory = OptionRecord(option(Accessory, fixed=5_000), False)
    rule = PricingRule(
        id=uuid4(),
        name="Ajuste de prueba",
        version=1,
        priority=10,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
        conditions={"field": "volumeMm3", "operator": "greater_than", "value": 100},
        operation={"type": "percentage", "value": 5},
        active=True,
        created_by=None,
        created_at=datetime.now(UTC),
    )
    pricing = PricingService(
        FakeCatalog(item_product),
        FakePricing(material, finish, [accessory], [rule]),
        clock=lambda: datetime(2026, 11, 21, tzinfo=UTC),
    )
    request = QuoteEstimateRequest(
        items=[
            EstimateItemRequest(
                product_id=item_product.id,
                width_mm=1000,
                height_mm=1000,
                depth_mm=500,
                material_id=material.option.id,
                finish_id=finish.option.id,
                accessory_ids=[accessory.option.id],
            )
        ]
    )

    estimate = pricing.estimate(request)

    assert estimate.subtotal_minor == 100_000
    assert estimate.adjustments_minor == 31_250
    assert estimate.total_minor == 131_250
    assert estimate.deposit_minor == 65_625
    assert estimate.items[0].breakdown.model_dump() == {
        "reference_base_minor": 100_000,
        "size_adjusted_base_minor": 100_000,
        "material_minor": 10_000,
        "finish_minor": 10_000,
        "accessories_minor": 5_000,
        "rules_minor": 6_250,
        "unit_total_minor": 131_250,
    }
    assert estimate.items[0].min_production_days == 8
    assert estimate.items[0].max_production_days == 11


def test_estimate_rejects_measurements_outside_product_range() -> None:
    item_product = product()
    pricing = PricingService(
        FakeCatalog(item_product),
        FakePricing(None, None, [], []),
    )
    request = QuoteEstimateRequest(
        items=[
            EstimateItemRequest(
                product_id=item_product.id,
                width_mm=999,
                height_mm=1000,
                depth_mm=500,
            )
        ]
    )

    with pytest.raises(PricingValidationError, match="widthMm"):
        pricing.estimate(request)


def test_estimate_rejects_accessory_not_available_for_product() -> None:
    item_product = product()
    pricing = PricingService(
        FakeCatalog(item_product),
        FakePricing(None, None, [], []),
    )
    request = QuoteEstimateRequest(
        items=[
            EstimateItemRequest(
                product_id=item_product.id,
                width_mm=1000,
                height_mm=1000,
                depth_mm=500,
                accessory_ids=[uuid4()],
            )
        ]
    )

    with pytest.raises(PricingValidationError, match="accesorios"):
        pricing.estimate(request)


def test_create_rule_versions_and_deactivates_previous_active_rule() -> None:
    item_product = product()
    previous = PricingRule(
        id=uuid4(),
        name="Ajuste por volumen",
        version=1,
        priority=100,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=None,
        conditions={"field": "volumeMm3", "operator": "greater_than", "value": 100},
        operation={"type": "percentage", "value": 5},
        active=True,
        created_by=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    repository = FakePricing(None, None, [], [previous])
    now = datetime(2026, 11, 21, tzinfo=UTC)
    service = PricingService(
        FakeCatalog(item_product), repository, clock=lambda: now
    )
    user_id = uuid4()

    created = service.create_rule(
        PricingRuleCreateRequest(
            name="Ajuste por volumen",
            condition=PricingConditionRequest(
                field="volumeMm3", operator="greater_or_equal", value=200
            ),
            operation=PricingOperationRequest(type="percentage", value=Decimal("7.5")),
        ),
        created_by=user_id,
    )

    assert created.version == 2
    assert created.created_by == user_id
    assert created.valid_from == now
    assert previous.active is False
    assert repository.deactivated_names == ["Ajuste por volumen"]
    assert repository.commits == 1
