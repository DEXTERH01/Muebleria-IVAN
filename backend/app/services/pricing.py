"""Deterministic and versioned quote estimation."""

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID, uuid4

from app.domain.catalog import PricingValidationError, ProductNotFoundError
from app.models.catalog import PricingRule, Product
from app.repositories.catalog import CatalogRepository, OptionRecord
from app.repositories.pricing import PricingRepository
from app.schemas.pricing import (
    AppliedRuleData,
    EstimateItemData,
    EstimateItemRequest,
    PricingBreakdownData,
    PricingConditionRequest,
    PricingOperationRequest,
    PricingRuleCreateRequest,
    PricingRuleData,
    QuoteEstimateData,
    QuoteEstimateRequest,
    SelectedOptionData,
)


def _round_minor(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class PricingService:
    def __init__(
        self,
        catalog: CatalogRepository,
        pricing: PricingRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.catalog = catalog
        self.pricing = pricing
        self.clock = clock or (lambda: datetime.now(UTC))

    def estimate(self, request: QuoteEstimateRequest) -> QuoteEstimateData:
        at = self.clock()
        rules = self.pricing.active_rules(at)
        items = [self._estimate_item(item, rules) for item in request.items]
        subtotal = sum(
            item.breakdown.size_adjusted_base_minor * item.quantity for item in items
        )
        total = sum(item.line_total_minor for item in items)
        adjustments = total - subtotal
        if total < 0:
            raise PricingValidationError("La combinación de ajustes produce un total inválido.")
        return QuoteEstimateData(
            subtotal_minor=subtotal,
            adjustments_minor=adjustments,
            total_minor=total,
            deposit_minor=(total + 1) // 2,
            items=items,
        )

    def list_rules(self) -> list[PricingRuleData]:
        return [self._rule_data(rule) for rule in self.pricing.all_rules()]

    def create_rule(
        self,
        request: PricingRuleCreateRequest,
        *,
        created_by: UUID,
    ) -> PricingRuleData:
        now = self.clock()
        valid_from = request.valid_from or now
        if valid_from.tzinfo is None:
            valid_from = valid_from.replace(tzinfo=UTC)
        valid_until = request.valid_until
        if valid_until and valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=UTC)
        if valid_until and valid_until <= valid_from:
            raise PricingValidationError("validUntil debe ser posterior a validFrom.")

        rule = PricingRule(
            id=uuid4(),
            name=request.name.strip(),
            version=self.pricing.next_version(request.name.strip()),
            priority=request.priority,
            valid_from=valid_from,
            valid_until=valid_until,
            conditions=request.condition.model_dump(mode="json", by_alias=True),
            operation=request.operation.model_dump(mode="json", by_alias=True),
            active=request.active,
            created_by=created_by,
            created_at=now,
        )
        try:
            if rule.active:
                self.pricing.deactivate_active_versions(rule.name)
            self.pricing.add(rule)
            self.pricing.commit()
        except Exception:
            self.pricing.rollback()
            raise
        return self._rule_data(rule)

    @staticmethod
    def _rule_data(rule: PricingRule) -> PricingRuleData:
        return PricingRuleData(
            id=rule.id,
            name=rule.name,
            version=rule.version,
            priority=rule.priority,
            valid_from=rule.valid_from,
            valid_until=rule.valid_until,
            condition=PricingConditionRequest.model_validate(rule.conditions),
            operation=PricingOperationRequest.model_validate(rule.operation),
            active=rule.active,
            created_by=rule.created_by,
            created_at=rule.created_at,
        )

    def _estimate_item(
        self, request: EstimateItemRequest, rules: list[PricingRule]
    ) -> EstimateItemData:
        product = self.catalog.get_by_id(request.product_id)
        if product is None:
            raise ProductNotFoundError("El producto solicitado no existe o no está activo.")
        self._validate_dimensions(product, request)

        material = self.pricing.material(product.id, request.material_id)
        if request.material_id is not None and material is None:
            raise PricingValidationError("El material no está disponible para este producto.")
        finish = self.pricing.finish(product.id, request.finish_id)
        if request.finish_id is not None and finish is None:
            raise PricingValidationError("El acabado no está disponible para este producto.")
        accessories = self.pricing.accessories(product.id, request.accessory_ids)
        if len(accessories) != len(request.accessory_ids):
            raise PricingValidationError("Uno o más accesorios no están disponibles.")

        size_factor = self._size_factor(product, request)
        size_base = _round_minor(Decimal(product.base_price_minor) * size_factor)
        material_minor = self._option_adjustment(material, size_base)
        finish_minor = self._option_adjustment(finish, size_base)
        accessories_minor = sum(
            self._option_adjustment(accessory, size_base) for accessory in accessories
        )
        before_rules = size_base + material_minor + finish_minor + accessories_minor
        applied_rules, rules_minor = self._apply_rules(
            rules,
            product=product,
            request=request,
            unit_subtotal=before_rules,
        )
        unit_total = before_rules + rules_minor
        if unit_total < 0:
            raise PricingValidationError("Los ajustes producen un precio unitario inválido.")

        extra_days = max(0, _round_minor((size_factor - Decimal(1)) * Decimal(2)))
        extra_days += (len(accessories) + 1) // 2
        return EstimateItemData(
            product_id=product.id,
            product_name=product.name,
            quantity=request.quantity,
            width_mm=request.width_mm,
            height_mm=request.height_mm,
            depth_mm=request.depth_mm,
            material=self._selected_option(material, material_minor),
            finish=self._selected_option(finish, finish_minor),
            accessories=[
                self._selected_option(option, self._option_adjustment(option, size_base))
                for option in accessories
            ],
            applied_rules=applied_rules,
            breakdown=PricingBreakdownData(
                reference_base_minor=product.base_price_minor,
                size_adjusted_base_minor=size_base,
                material_minor=material_minor,
                finish_minor=finish_minor,
                accessories_minor=accessories_minor,
                rules_minor=rules_minor,
                unit_total_minor=unit_total,
            ),
            line_total_minor=unit_total * request.quantity,
            min_production_days=product.min_production_days + extra_days,
            max_production_days=product.max_production_days + extra_days,
        )

    @staticmethod
    def _validate_dimensions(product: Product, request: EstimateItemRequest) -> None:
        for dimension in ("width", "height", "depth"):
            value = getattr(request, f"{dimension}_mm")
            minimum = getattr(product, f"min_{dimension}_mm")
            maximum = getattr(product, f"max_{dimension}_mm")
            if not minimum <= value <= maximum:
                raise PricingValidationError(
                    f"{dimension}Mm debe estar entre {minimum} y {maximum}."
                )

    @staticmethod
    def _size_factor(product: Product, request: EstimateItemRequest) -> Decimal:
        ratios = [
            Decimal(request.width_mm) / Decimal(product.min_width_mm),
            Decimal(request.height_mm) / Decimal(product.min_height_mm),
            Decimal(request.depth_mm) / Decimal(product.min_depth_mm),
        ]
        return sum(ratios, start=Decimal(0)) / Decimal(3)

    @staticmethod
    def _option_adjustment(option: OptionRecord | None, base_minor: int) -> int:
        if option is None:
            return 0
        percentage = (
            Decimal(base_minor) * option.option.price_adjustment_percent / Decimal(100)
        )
        return option.option.price_adjustment_minor + _round_minor(percentage)

    @staticmethod
    def _selected_option(
        record: OptionRecord | None, adjustment_minor: int
    ) -> SelectedOptionData | None:
        if record is None:
            return None
        return SelectedOptionData(
            id=record.option.id,
            code=str(record.option.code),
            name=record.option.name,
            adjustment_minor=adjustment_minor,
        )

    def _apply_rules(
        self,
        rules: list[PricingRule],
        *,
        product: Product,
        request: EstimateItemRequest,
        unit_subtotal: int,
    ) -> tuple[list[AppliedRuleData], int]:
        context: dict[str, Any] = {
            "volumeMm3": request.width_mm * request.height_mm * request.depth_mm,
            "quantity": request.quantity,
            "category": product.category,
            "subtotalMinor": unit_subtotal,
        }
        applied: list[AppliedRuleData] = []
        total = 0
        for rule in rules:
            if not self._condition_matches(rule.conditions, context):
                continue
            adjustment = self._operation_amount(rule.operation, unit_subtotal)
            total += adjustment
            applied.append(
                AppliedRuleData(
                    id=rule.id,
                    name=rule.name,
                    version=rule.version,
                    adjustment_minor=adjustment,
                )
            )
        return applied, total

    @staticmethod
    def _condition_matches(condition: dict[str, Any], context: dict[str, Any]) -> bool:
        field = condition.get("field")
        operator = condition.get("operator")
        expected = condition.get("value")
        if field not in context:
            raise PricingValidationError(f"La regla usa el campo no soportado: {field}.")
        actual = context[field]
        operations: dict[str, Callable[[Any, Any], bool]] = {
            "equals": lambda left, right: left == right,
            "greater_than": lambda left, right: left > right,
            "greater_or_equal": lambda left, right: left >= right,
            "less_than": lambda left, right: left < right,
            "less_or_equal": lambda left, right: left <= right,
            "in": lambda left, right: left in right,
        }
        if operator not in operations:
            raise PricingValidationError(f"La regla usa el operador no soportado: {operator}.")
        try:
            return operations[operator](actual, expected)
        except TypeError as exc:
            raise PricingValidationError(
                "La condición de precio tiene valores incompatibles."
            ) from exc

    @staticmethod
    def _operation_amount(operation: dict[str, Any], base_minor: int) -> int:
        operation_type = operation.get("type")
        try:
            value = Decimal(str(operation["value"]))
        except (KeyError, ValueError) as exc:
            raise PricingValidationError(
                "La operación de precio no tiene un valor válido."
            ) from exc
        if operation_type == "percentage":
            return _round_minor(Decimal(base_minor) * value / Decimal(100))
        if operation_type == "fixed_minor":
            return _round_minor(value)
        raise PricingValidationError(
            f"La regla usa la operación no soportada: {operation_type}."
        )
