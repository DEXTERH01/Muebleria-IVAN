"""Quote persistence, ownership checks, and status transitions."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.security import CurrentUser
from app.domain.catalog import (
    InvalidQuoteTransitionError,
    QuoteAccessError,
    QuoteNotFoundError,
    QuoteVersionConflictError,
)
from app.models.quotes import Quote, QuoteItem
from app.repositories.quotes import QuoteAggregate, QuoteRepository
from app.schemas.pricing import PricingBreakdownData, QuoteEstimateRequest, SelectedOptionData
from app.schemas.quotes import (
    QuoteCreateRequest,
    QuoteData,
    QuoteItemData,
    QuoteStatusUpdateRequest,
)
from app.services.pricing import PricingService

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "submitted": {"reviewing", "approved", "rejected", "expired"},
    "reviewing": {"approved", "rejected", "expired"},
    "approved": {"expired"},
    "rejected": set(),
    "expired": set(),
    "converted": set(),
    "draft": {"submitted"},
}


class QuoteService:
    def __init__(
        self,
        repository: QuoteRepository,
        pricing: PricingService,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.pricing = pricing
        self.clock = clock or (lambda: datetime.now(UTC))

    def create(self, request: QuoteCreateRequest, owner: CurrentUser | None) -> QuoteData:
        now = self.clock()
        estimate = self.pricing.estimate(QuoteEstimateRequest(items=request.items))
        quote_id = uuid4()
        quote = Quote(
            id=quote_id,
            code=f"COT-{now.year}-{quote_id.hex[:8].upper()}",
            customer_id=None,
            owner_user_id=owner.user_id if owner else None,
            contact_name=request.contact_name.strip(),
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            status="submitted",
            currency="PEN",
            subtotal_minor=estimate.subtotal_minor,
            adjustments_minor=estimate.adjustments_minor,
            total_minor=estimate.total_minor,
            deposit_minor=estimate.deposit_minor,
            expires_at=now + timedelta(days=7),
            version=1,
            created_at=now,
            updated_at=now,
        )
        items = [
            self._new_item(quote_id, requested, calculated, now)
            for requested, calculated in zip(request.items, estimate.items, strict=True)
        ]
        try:
            self.repository.add(quote, items)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
        return self._data(QuoteAggregate(quote=quote, items=items))

    def get(self, quote_id: UUID, user: CurrentUser) -> QuoteData:
        aggregate = self.repository.get(quote_id)
        if aggregate is None:
            raise QuoteNotFoundError("La cotización solicitada no existe.")
        if user.role != "admin" and aggregate.quote.owner_user_id != user.user_id:
            raise QuoteAccessError("No tienes permiso para consultar esta cotización.")
        return self._data(aggregate)

    def update_status(
        self,
        quote_id: UUID,
        request: QuoteStatusUpdateRequest,
    ) -> QuoteData:
        aggregate = self.repository.get(quote_id)
        if aggregate is None:
            raise QuoteNotFoundError("La cotización solicitada no existe.")
        current = aggregate.quote.status
        if request.status not in ALLOWED_TRANSITIONS.get(current, set()):
            raise InvalidQuoteTransitionError(
                f"La cotización no puede pasar de {current} a {request.status}."
            )
        updated = self.repository.update_status(
            quote_id,
            expected_version=request.expected_version,
            new_status=request.status,
        )
        if updated is None:
            self.repository.rollback()
            raise QuoteVersionConflictError(
                "La cotización fue modificada por otra operación; vuelve a cargarla."
            )
        self.repository.commit()
        return self._data(QuoteAggregate(quote=updated, items=aggregate.items))

    @staticmethod
    def _new_item(quote_id, requested, calculated, now: datetime) -> QuoteItem:
        pricing_snapshot = calculated.breakdown.model_dump(mode="json", by_alias=True)
        calculation_snapshot = {
            "pricing": pricing_snapshot,
            "material": calculated.material.model_dump(mode="json", by_alias=True)
            if calculated.material
            else None,
            "finish": calculated.finish.model_dump(mode="json", by_alias=True)
            if calculated.finish
            else None,
            "appliedRules": [
                rule.model_dump(mode="json", by_alias=True) for rule in calculated.applied_rules
            ],
        }
        return QuoteItem(
            id=uuid4(),
            quote_id=quote_id,
            product_id=calculated.product_id,
            quantity=calculated.quantity,
            width_mm=calculated.width_mm,
            height_mm=calculated.height_mm,
            depth_mm=calculated.depth_mm,
            material_id=calculated.material.id if calculated.material else None,
            finish_id=calculated.finish.id if calculated.finish else None,
            accessories=[
                option.model_dump(mode="json", by_alias=True)
                for option in calculated.accessories
            ],
            configuration=requested.configuration,
            product_name_snapshot=calculated.product_name,
            base_price_minor=calculated.breakdown.reference_base_minor,
            calculation_breakdown=calculation_snapshot,
            line_total_minor=calculated.line_total_minor,
            created_at=now,
        )

    @staticmethod
    def _data(aggregate: QuoteAggregate) -> QuoteData:
        quote = aggregate.quote
        items = []
        for item in aggregate.items:
            snapshot = item.calculation_breakdown
            pricing = snapshot.get("pricing", snapshot)
            items.append(
                QuoteItemData(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name_snapshot,
                    quantity=item.quantity,
                    width_mm=item.width_mm,
                    height_mm=item.height_mm,
                    depth_mm=item.depth_mm,
                    material=SelectedOptionData.model_validate(snapshot["material"])
                    if snapshot.get("material")
                    else None,
                    finish=SelectedOptionData.model_validate(snapshot["finish"])
                    if snapshot.get("finish")
                    else None,
                    accessories=[
                        SelectedOptionData.model_validate(option) for option in item.accessories
                    ],
                    configuration=item.configuration,
                    base_price_minor=item.base_price_minor,
                    breakdown=PricingBreakdownData.model_validate(pricing),
                    line_total_minor=item.line_total_minor,
                )
            )
        return QuoteData(
            id=quote.id,
            code=str(quote.code),
            status=quote.status,
            currency=quote.currency,
            contact_name=quote.contact_name,
            contact_email=str(quote.contact_email) if quote.contact_email else None,
            contact_phone=quote.contact_phone,
            subtotal_minor=quote.subtotal_minor,
            adjustments_minor=quote.adjustments_minor,
            total_minor=quote.total_minor,
            deposit_minor=quote.deposit_minor,
            expires_at=quote.expires_at,
            version=quote.version,
            created_at=quote.created_at,
            updated_at=quote.updated_at,
            items=items,
        )
