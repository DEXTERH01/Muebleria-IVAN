"""Central model registry.

Import all SQLAlchemy models here so that:
1. app.models.__init__ is the single import point for other modules.
2. Base.metadata has all tables registered before create_all / inspection.
3. models/__init__.py is the integration point owned by Dexter
   (see docs/PLAN_TRABAJO_PARALELO.md § Archivos de integración).

Models owned by Cristian (products, quotes) will be added here when
codex/database-catalog is merged into main.
"""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.customer import Customer
from app.models.delivery_location import DeliveryLocation
from app.models.media_asset import MediaAsset
from app.models.model_version import ModelVersion
from app.models.optimization_run import OptimizationRun
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_event import OrderStatusEvent
from app.models.payment import Payment
from app.models.prediction import Prediction
from app.models.production_job import ProductionJob
from app.models.profile import Profile

__all__ = [
    "AuditLog",
    "Base",
    "Customer",
    "DeliveryLocation",
    "MediaAsset",
    "ModelVersion",
    "OptimizationRun",
    "Order",
    "OrderItem",
    "OrderStatusEvent",
    "Payment",
    "Prediction",
    "ProductionJob",
    "Profile",
]
