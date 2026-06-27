from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SerializerMixin:
    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            result[column.name] = value
        return result


class User(Base, TimestampMixin, SerializerMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Company(Base, TimestampMixin, SerializerMixin):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    address: Mapped[str] = mapped_column(Text, default="")
    gst_number: Mapped[str] = mapped_column(String(15), default="")
    financial_year: Mapped[str] = mapped_column(String(9))
    contact_information: Mapped[str] = mapped_column(String(255), default="")
    state: Mapped[str] = mapped_column(String(100))


class CompanyEntityMixin:
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)


class Group(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("company_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(20))  # Assets/Liabilities/Income/Expenses


class Ledger(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "ledgers"
    __table_args__ = (UniqueConstraint("company_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    ledger_type: Mapped[str] = mapped_column(String(20))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)


class StockGroup(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "stock_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))


class Unit(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    symbol: Mapped[str] = mapped_column(String(12))


class StockItem(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "stock_items"
    __table_args__ = (UniqueConstraint("company_id", "sku"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    sku: Mapped[str] = mapped_column(String(80))
    hsn_code: Mapped[str] = mapped_column(String(20), default="")
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    reserved_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    damaged_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    gst_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    stock_group_id: Mapped[int | None] = mapped_column(ForeignKey("stock_groups.id"), nullable=True)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)


class PartyMixin:
    name: Mapped[str] = mapped_column(String(160))
    gst: Mapped[str] = mapped_column(String(15), default="")
    mobile: Mapped[str] = mapped_column(String(20), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    ledger_id: Mapped[int | None] = mapped_column(ForeignKey("ledgers.id"), nullable=True)


class Customer(Base, CompanyEntityMixin, PartyMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)


class Supplier(Base, CompanyEntityMixin, PartyMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)


class Purchase(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(primary_key=True)
    voucher_number: Mapped[str] = mapped_column(String(40))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    voucher_date: Mapped[date] = mapped_column(Date, default=date.today)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    notes: Mapped[str] = mapped_column(Text, default="")


class Sale(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(primary_key=True)
    voucher_number: Mapped[str] = mapped_column(String(40))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    voucher_date: Mapped[date] = mapped_column(Date, default=date.today)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    notes: Mapped[str] = mapped_column(Text, default="")


class Invoice(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, default=date.today)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))


class VoucherEntry(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "voucher_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    voucher_type: Mapped[str] = mapped_column(String(20))
    voucher_number: Mapped[str] = mapped_column(String(40))
    voucher_date: Mapped[date] = mapped_column(Date, default=date.today)
    ledger_id: Mapped[int] = mapped_column(ForeignKey("ledgers.id"))
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    narration: Mapped[str] = mapped_column(Text, default="")
    reference_type: Mapped[str] = mapped_column(String(20), default="")
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class InventoryTransaction(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "inventory_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"))
    transaction_type: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    gst_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    from_location: Mapped[str] = mapped_column(String(120), default="")
    to_location: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    reference_type: Mapped[str] = mapped_column(String(20), default="")
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class GSTRecord(Base, CompanyEntityMixin, TimestampMixin, SerializerMixin):
    __tablename__ = "gst_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    record_type: Mapped[str] = mapped_column(String(20))
    reference_id: Mapped[int] = mapped_column(Integer)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    gst_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    record_date: Mapped[date] = mapped_column(Date, default=date.today)


class AuditLog(Base, TimestampMixin, SerializerMixin):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(30))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
