
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)

from app.database import Base


class Product(Base):
    """
    Represents a product maintained in the inventory catalog.
    """

    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint(
            "stock_quantity >= 0",
            name="ck_products_stock_non_negative",
        ),
        CheckConstraint(
            "base_price_usd >= 0",
            name="ck_products_price_non_negative",
        ),
    )

    sku = Column(
        String(100),
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    stock_quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )

    warehouse_location = Column(
        String(255),
        nullable=False,
    )

    base_price_usd = Column(
        Float,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self):
        return (
            f"Product(sku={self.sku!r}, "
            f"name={self.name!r}, "
            f"stock_quantity={self.stock_quantity})"
        )


class ReconciliationAuditLog(Base):
    """
    Stores the execution history of inventory reconciliation jobs.
    """

    __tablename__ = "reconciliation_audit_logs"

    __table_args__ = (
        CheckConstraint(
            "status IN ('SUCCESS', 'RETRY_FALLBACK', 'FAILED')",
            name="ck_audit_status_valid",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    status = Column(
        String(30),
        nullable=False,
    )

    skus_processed = Column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    def __repr__(self):
        return (
            f"ReconciliationAuditLog("
            f"id={self.id}, "
            f"status={self.status!r}, "
            f"skus_processed={self.skus_processed})"
        )
