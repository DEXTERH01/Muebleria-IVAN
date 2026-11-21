"""Shared API schema conventions for commercial modules."""

from pydantic import BaseModel, ConfigDict


def to_camel(field_name: str) -> str:
    first, *rest = field_name.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )
