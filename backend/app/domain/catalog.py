"""Domain errors and state transitions owned by catalog and quotes."""


class CatalogError(Exception):
    pass


class ProductNotFoundError(CatalogError):
    pass


class DuplicateProductError(CatalogError):
    pass


class PricingValidationError(CatalogError):
    pass


class QuoteNotFoundError(CatalogError):
    pass


class QuoteAccessError(CatalogError):
    pass


class QuoteVersionConflictError(CatalogError):
    pass


class InvalidQuoteTransitionError(CatalogError):
    pass
