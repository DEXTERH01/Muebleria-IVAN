"""Queries required by the deterministic pricing service."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.models.catalog import (
    Accessory,
    Finish,
    Material,
    PricingRule,
    ProductAccessory,
    ProductFinish,
    ProductMaterial,
)
from app.repositories.catalog import OptionRecord


class PricingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def material(self, product_id: UUID, option_id: UUID | None) -> OptionRecord | None:
        statement = (
            select(Material, ProductMaterial.is_default)
            .join(ProductMaterial, ProductMaterial.material_id == Material.id)
            .where(
                ProductMaterial.product_id == product_id,
                Material.active.is_(True),
                Material.available.is_(True),
            )
        )
        if option_id is None:
            statement = statement.where(ProductMaterial.is_default.is_(True))
        else:
            statement = statement.where(Material.id == option_id)
        row = self.session.execute(statement).one_or_none()
        return OptionRecord(row[0], row[1]) if row else None

    def finish(self, product_id: UUID, option_id: UUID | None) -> OptionRecord | None:
        statement = (
            select(Finish, ProductFinish.is_default)
            .join(ProductFinish, ProductFinish.finish_id == Finish.id)
            .where(
                ProductFinish.product_id == product_id,
                Finish.active.is_(True),
                Finish.available.is_(True),
            )
        )
        if option_id is None:
            statement = statement.where(ProductFinish.is_default.is_(True))
        else:
            statement = statement.where(Finish.id == option_id)
        row = self.session.execute(statement).one_or_none()
        return OptionRecord(row[0], row[1]) if row else None

    def accessories(self, product_id: UUID, option_ids: list[UUID]) -> list[OptionRecord]:
        if not option_ids:
            return []
        rows = self.session.execute(
            select(Accessory, ProductAccessory.is_default)
            .join(ProductAccessory, ProductAccessory.accessory_id == Accessory.id)
            .where(
                ProductAccessory.product_id == product_id,
                Accessory.id.in_(option_ids),
                Accessory.active.is_(True),
                Accessory.available.is_(True),
            )
            .order_by(Accessory.name)
        ).all()
        return [OptionRecord(row[0], row[1]) for row in rows]

    def active_rules(self, at: datetime) -> list[PricingRule]:
        return list(
            self.session.scalars(
                select(PricingRule)
                .where(
                    PricingRule.active.is_(True),
                    PricingRule.valid_from <= at,
                    or_(PricingRule.valid_until.is_(None), PricingRule.valid_until > at),
                )
                .order_by(PricingRule.priority, PricingRule.name, PricingRule.version.desc())
            ).all()
        )

    def all_rules(self) -> list[PricingRule]:
        return list(
            self.session.scalars(
                select(PricingRule).order_by(
                    PricingRule.name, PricingRule.version.desc(), PricingRule.id
                )
            ).all()
        )

    def next_version(self, name: str) -> int:
        latest = self.session.scalar(
            select(func.max(PricingRule.version)).where(PricingRule.name == name)
        )
        return (latest or 0) + 1

    def deactivate_active_versions(self, name: str) -> None:
        self.session.execute(
            update(PricingRule)
            .where(PricingRule.name == name, PricingRule.active.is_(True))
            .values(active=False)
        )

    def add(self, rule: PricingRule) -> None:
        self.session.add(rule)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
