"""PostgreSQL types supplied by Supabase extensions."""

from sqlalchemy.types import UserDefinedType


class ExtensionCITEXT(UserDefinedType[str]):
    """Case-insensitive text type installed in the Supabase extensions schema."""

    cache_ok = True

    def get_col_spec(self, **_kw: object) -> str:
        return "extensions.citext"
