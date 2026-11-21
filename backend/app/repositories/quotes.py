"""Persistence operations for quote snapshots and optimistic updates."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.quotes import Quote, QuoteItem


@dataclass(frozen=True)
class QuoteAggregate:
    quote: Quote
    items: list[QuoteItem]


class QuoteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, quote: Quote, items: list[QuoteItem]) -> None:
        self.session.add(quote)
        self.session.add_all(items)
        self.session.flush()

    def get(self, quote_id: UUID) -> QuoteAggregate | None:
        quote = self.session.get(Quote, quote_id)
        if quote is None:
            return None
        items = list(
            self.session.scalars(
                select(QuoteItem)
                .where(QuoteItem.quote_id == quote_id)
                .order_by(QuoteItem.created_at, QuoteItem.id)
            ).all()
        )
        return QuoteAggregate(quote=quote, items=items)

    def update_status(
        self,
        quote_id: UUID,
        *,
        expected_version: int,
        new_status: str,
    ) -> Quote | None:
        return self.session.scalar(
            update(Quote)
            .where(Quote.id == quote_id, Quote.version == expected_version)
            .values(status=new_status, version=Quote.version + 1)
            .returning(Quote)
        )

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
