from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.repositories.catalog import CatalogRepository


class Rows(list):
    def all(self):
        return self


def test_get_aggregates_batches_options_and_images_for_the_product_page() -> None:
    first_id = uuid4()
    second_id = uuid4()
    first = SimpleNamespace(id=first_id)
    second = SimpleNamespace(id=second_id)
    material = SimpleNamespace(id=uuid4(), name="Melamina")
    image = SimpleNamespace(id=uuid4(), product_id=first_id, position=0)
    session = Mock()
    session.execute.side_effect = [
        Rows([(first_id, material, True)]),
        Rows([]),
        Rows([]),
    ]
    session.scalars.return_value.all.return_value = Rows([image])

    aggregates = CatalogRepository(session).get_aggregates([first, second])

    assert [aggregate.product.id for aggregate in aggregates] == [first_id, second_id]
    assert aggregates[0].materials[0].option is material
    assert aggregates[0].materials[0].is_default is True
    assert aggregates[0].images == [image]
    assert aggregates[1].materials == []
    assert aggregates[1].images == []
    assert session.execute.call_count == 3
    assert session.scalars.call_count == 1


def test_get_aggregates_returns_without_queries_for_an_empty_page() -> None:
    session = Mock()

    assert CatalogRepository(session).get_aggregates([]) == []
    session.execute.assert_not_called()
    session.scalars.assert_not_called()
