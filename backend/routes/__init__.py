from datetime import date
from io import BytesIO

from flask import Blueprint, g, request, send_file
from flask_jwt_extended import create_access_token
from openpyxl import Workbook
from sqlalchemy import case, extract, func, select

from auth import hash_password, verify_password
from controllers import create_entity, delete_entity, list_entities, update_entity
from database import Session
from middleware import audit, authenticated, company_required
from models import (
    AuditLog, Company, Customer, Group, GSTRecord, InventoryTransaction, Invoice, Ledger, Purchase,
    Sale, StockGroup, StockItem, Supplier, Unit, User, VoucherEntry
)
from schemas import ValidationError, positive, require
from services import create_trade, invoice_pdf, next_number

api = Blueprint("api", __name__, url_prefix="/api")


@api.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    require(data, "email", "password", "full_name")
    email = data["email"].strip().lower()
    if Session.scalar(select(User).where(User.email == email)):
        return {"error": "Email already registered"}, 409
    if len(data["password"]) < 8:
        return {"error": "Password must contain at least 8 characters"}, 400
    user = User(email=email, password_hash=hash_password(data["password"]), full_name=data["full_name"])
    Session.add(user)
    Session.commit()
    return {"user": user.to_dict(), "access_token": create_access_token(str(user.id))}, 201


@api.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    require(data, "email", "password")
    user = Session.scalar(select(User).where(User.email == data["email"].strip().lower()))
    if not user or not user.is_active or not verify_password(data["password"], user.password_hash):
        return {"error": "Invalid email or password"}, 401
    return {"user": user.to_dict(), "access_token": create_access_token(str(user.id))}


@api.get("/auth/me")
@authenticated
def me():
    return Session.get(User, g.user_id).to_dict()


COMPANY_FIELDS = ("name", "address", "gst_number", "financial_year", "contact_information", "state")


@api.get("/companies")
@authenticated
def companies():
    return {"items": [x.to_dict() for x in Session.scalars(select(Company).order_by(Company.name)).all()]}


@api.post("/companies")
@authenticated
def create_company():
    data = request.get_json(silent=True) or {}
    require(data, "name", "financial_year", "state")
    company = Company(**{k: data.get(k, "") for k in COMPANY_FIELDS})
    Session.add(company)
    Session.flush()
    for name, category in (("Cash", "Assets"), ("Bank", "Assets"), ("Sales", "Income"), ("Purchases", "Expenses")):
        group = Group(company_id=company.id, name=category, category=category)
        existing = Session.scalar(select(Group).where(Group.company_id == company.id, Group.name == category))
        if not existing:
            Session.add(group)
            Session.flush()
            existing = group
        Session.add(Ledger(company_id=company.id, name=name, ledger_type=name.lower(), group_id=existing.id))
    for name in ("Electronics", "Furniture", "Medical", "Grocery"):
        Session.add(StockGroup(company_id=company.id, name=name))
    for name, symbol in (("Pieces", "PCS"), ("Box", "BOX"), ("Kilogram", "KG"), ("Litre", "LTR")):
        Session.add(Unit(company_id=company.id, name=name, symbol=symbol))
    Session.add(AuditLog(user_id=g.user_id, company_id=company.id, action="CREATE", entity_type="companies", entity_id=company.id))
    Session.commit()
    return company.to_dict(), 201


@api.put("/companies/<int:entity_id>")
@authenticated
def update_company(entity_id):
    company = Session.get(Company, entity_id)
    if not company:
        return {"error": "Not found"}, 404
    data = request.get_json(silent=True) or {}
    for field in COMPANY_FIELDS:
        if field in data:
            setattr(company, field, data[field])
    Session.commit()
    return company.to_dict()


@api.delete("/companies/<int:entity_id>")
@authenticated
def remove_company(entity_id):
    company = Session.get(Company, entity_id)
    if not company:
        return {"error": "Not found"}, 404
    Session.delete(company)
    Session.commit()
    return "", 204


RESOURCE_MAP = {
    "groups": (Group, ("name", "category"), ("name", "category")),
    "ledgers": (Ledger, ("name", "ledger_type", "group_id", "opening_balance"), ("name", "ledger_type")),
    "stock-groups": (StockGroup, ("name",), ("name",)),
    "units": (Unit, ("name", "symbol"), ("name", "symbol")),
    "stock-items": (StockItem, ("name", "sku", "hsn_code", "purchase_price", "selling_price", "quantity", "reserved_stock", "damaged_stock", "reorder_level", "gst_percent", "stock_group_id", "unit_id"), ("name", "sku")),
    "customers": (Customer, ("name", "gst", "mobile", "address", "outstanding_balance", "ledger_id"), ("name",)),
    "suppliers": (Supplier, ("name", "gst", "mobile", "address", "outstanding_balance", "ledger_id"), ("name",)),
}


def register_resource(name, model, fields, required):
    endpoint = name.replace("-", "_")

    @api.get(f"/{name}", endpoint=f"{endpoint}_list")
    @company_required
    def resource_list():
        return list_entities(model)

    @api.post(f"/{name}", endpoint=f"{endpoint}_create")
    @company_required
    def resource_create():
        return create_entity(model, fields, required)

    @api.put(f"/{name}/<int:entity_id>", endpoint=f"{endpoint}_update")
    @company_required
    def resource_update(entity_id):
        return update_entity(model, entity_id, fields)

    @api.delete(f"/{name}/<int:entity_id>", endpoint=f"{endpoint}_delete")
    @company_required
    def resource_delete(entity_id):
        return delete_entity(model, entity_id)


for resource_name, resource_config in RESOURCE_MAP.items():
    register_resource(resource_name, *resource_config)


@api.get("/purchases")
@company_required
def purchases():
    return {"items": [x.to_dict() for x in Session.scalars(
        select(Purchase).where(Purchase.company_id == g.company_id).order_by(Purchase.id.desc())
    ).all()]}


@api.post("/purchases")
@company_required
def add_purchase():
    result = create_trade("purchase", g.company_id, request.get_json(silent=True) or {})
    audit("CREATE", "purchases", result["id"])
    Session.commit()
    return result, 201


@api.get("/sales")
@company_required
def sales():
    return {"items": [x.to_dict() for x in Session.scalars(
        select(Sale).where(Sale.company_id == g.company_id).order_by(Sale.id.desc())
    ).all()]}


@api.post("/sales")
@company_required
def add_sale():
    result = create_trade("sale", g.company_id, request.get_json(silent=True) or {})
    audit("CREATE", "sales", result["id"])
    Session.commit()
    return result, 201


@api.get("/invoices")
@company_required
def invoices():
    return {"items": [x.to_dict() for x in Session.scalars(
        select(Invoice).where(Invoice.company_id == g.company_id).order_by(Invoice.id.desc())
    ).all()]}


@api.get("/invoices/<int:invoice_id>")
@company_required
def invoice_detail(invoice_id):
    invoice = Session.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != g.company_id:
        return {"error": "Not found"}, 404
    sale = Session.get(Sale, invoice.sale_id)
    customer = Session.get(Customer, sale.customer_id)
    lines = Session.scalars(select(InventoryTransaction).where(
        InventoryTransaction.reference_type == "sale", InventoryTransaction.reference_id == sale.id
    )).all()
    return {"invoice": invoice.to_dict(), "sale": sale.to_dict(), "customer": customer.to_dict(),
            "items": [dict(x.to_dict(), item=Session.get(StockItem, x.item_id).to_dict()) for x in lines]}


@api.get("/invoices/<int:invoice_id>/pdf")
@company_required
def download_invoice(invoice_id):
    return send_file(invoice_pdf(invoice_id, g.company_id), mimetype="application/pdf",
                     as_attachment=True, download_name=f"invoice-{invoice_id}.pdf")


@api.get("/inventory/transactions")
@company_required
def inventory_transactions():
    return {"items": [x.to_dict() for x in Session.scalars(select(InventoryTransaction).where(
        InventoryTransaction.company_id == g.company_id
    ).order_by(InventoryTransaction.id.desc())).all()]}


@api.post("/inventory/transactions")
@company_required
def inventory_transaction():
    data = request.get_json(silent=True) or {}
    require(data, "item_id", "transaction_type", "quantity")
    item = Session.get(StockItem, int(data["item_id"]))
    if not item or item.company_id != g.company_id:
        raise ValidationError("Invalid item")
    qty = positive(data["quantity"], "quantity")
    kind = data["transaction_type"].upper()
    if kind not in ("STOCK_IN", "STOCK_OUT", "ADJUSTMENT", "TRANSFER", "DAMAGED", "RESERVED"):
        raise ValidationError("Invalid transaction_type")
    signed = qty if kind in ("STOCK_IN",) else -qty if kind == "STOCK_OUT" else qty
    if kind == "ADJUSTMENT":
        signed = float(data.get("adjustment", qty))
    if kind == "DAMAGED":
        item.damaged_stock += qty
        signed = -qty
    elif kind == "RESERVED":
        item.reserved_stock += qty
        signed = 0
    elif kind != "TRANSFER":
        if item.quantity + signed < 0:
            raise ValidationError("Insufficient stock")
        item.quantity += signed
    transaction = InventoryTransaction(
        company_id=g.company_id, item_id=item.id, transaction_type=kind, quantity=signed,
        unit_price=data.get("unit_price", item.purchase_price), gst_percent=item.gst_percent,
        from_location=data.get("from_location", ""), to_location=data.get("to_location", ""),
        notes=data.get("notes", "")
    )
    Session.add(transaction)
    Session.flush()
    audit("CREATE", "inventory_transactions", transaction.id)
    Session.commit()
    return transaction.to_dict(), 201


@api.get("/parties/<party_type>/<int:party_id>/statement")
@company_required
def party_statement(party_type, party_id):
    model = Customer if party_type == "customers" else Supplier if party_type == "suppliers" else None
    party = Session.get(model, party_id) if model else None
    if not party or party.company_id != g.company_id:
        return {"error": "Not found"}, 404
    entries = [] if not party.ledger_id else Session.scalars(select(VoucherEntry).where(
        VoucherEntry.company_id == g.company_id, VoucherEntry.ledger_id == party.ledger_id
    ).order_by(VoucherEntry.voucher_date, VoucherEntry.id)).all()
    balance = float(party.opening_balance) if hasattr(party, "opening_balance") else 0
    rows = []
    for entry in entries:
        balance += float(entry.debit - entry.credit)
        rows.append(dict(entry.to_dict(), balance=balance))
    return {"party": party.to_dict(), "entries": rows, "closing_balance": balance}


@api.post("/vouchers")
@company_required
def create_voucher():
    data = request.get_json(silent=True) or {}
    require(data, "voucher_type", "entries")
    if len(data["entries"]) < 2:
        raise ValidationError("A voucher requires at least two entries")
    debit = sum(float(x.get("debit", 0)) for x in data["entries"])
    credit = sum(float(x.get("credit", 0)) for x in data["entries"])
    if round(debit, 2) != round(credit, 2):
        raise ValidationError("Voucher debits and credits must balance")
    number = next_number(VoucherEntry, g.company_id, data["voucher_type"][:3].upper())
    rows = []
    for line in data["entries"]:
        ledger = Session.get(Ledger, int(line["ledger_id"]))
        if not ledger or ledger.company_id != g.company_id:
            raise ValidationError("Invalid ledger")
        row = VoucherEntry(company_id=g.company_id, voucher_type=data["voucher_type"].upper(),
                           voucher_number=number, voucher_date=data.get("voucher_date", date.today()),
                           ledger_id=ledger.id, debit=line.get("debit", 0), credit=line.get("credit", 0),
                           narration=data.get("narration", ""))
        Session.add(row)
        rows.append(row)
    Session.flush()
    audit("CREATE", "voucher_entries", rows[0].id, number)
    Session.commit()
    return {"voucher_number": number, "entries": [x.to_dict() for x in rows]}, 201


def report_data(report):
    cid = g.company_id
    if report in ("trial-balance", "balance-sheet", "profit-loss"):
        rows = Session.execute(select(
            Ledger.id, Ledger.name, Ledger.ledger_type,
            (Ledger.opening_balance + func.coalesce(func.sum(VoucherEntry.debit - VoucherEntry.credit), 0)).label("balance")
        ).outerjoin(VoucherEntry, VoucherEntry.ledger_id == Ledger.id).where(
            Ledger.company_id == cid
        ).group_by(Ledger.id)).all()
        items = [{"id": r.id, "name": r.name, "type": r.ledger_type, "balance": float(r.balance)} for r in rows]
        if report == "balance-sheet":
            items = [x for x in items if x["type"] in ("asset", "liability", "bank", "cash")]
        elif report == "profit-loss":
            items = [x for x in items if x["type"] in ("income", "expense", "sales", "purchase")]
        return items
    if report in ("stock-summary", "low-stock"):
        query = select(StockItem).where(StockItem.company_id == cid)
        if report == "low-stock":
            query = query.where(StockItem.quantity <= StockItem.reorder_level)
        return [dict(x.to_dict(), valuation=float(x.quantity * x.purchase_price)) for x in Session.scalars(query).all()]
    if report in ("daily-sales", "monthly-sales"):
        period = Sale.voucher_date if report == "daily-sales" else extract("month", Sale.voucher_date)
        rows = Session.execute(select(period.label("period"), func.sum(Sale.total).label("total")).where(
            Sale.company_id == cid
        ).group_by(period).order_by(period)).all()
        return [{"period": str(x.period), "total": float(x.total)} for x in rows]
    if report in ("purchase-register", "supplier-summary"):
        if report == "purchase-register":
            return [x.to_dict() for x in Session.scalars(select(Purchase).where(Purchase.company_id == cid)).all()]
        rows = Session.execute(select(Supplier.id, Supplier.name, Supplier.outstanding_balance,
            func.coalesce(func.sum(Purchase.total), 0).label("purchases")).outerjoin(
            Purchase, Purchase.supplier_id == Supplier.id
        ).where(Supplier.company_id == cid).group_by(Supplier.id)).all()
        return [{"id": x.id, "name": x.name, "outstanding": float(x.outstanding_balance), "purchases": float(x.purchases)} for x in rows]
    if report == "cash-flow":
        rows = Session.execute(select(VoucherEntry.voucher_date,
            func.sum(VoucherEntry.debit).label("inflow"), func.sum(VoucherEntry.credit).label("outflow")
        ).join(Ledger).where(Ledger.company_id == cid, Ledger.ledger_type.in_(("cash", "bank"))
        ).group_by(VoucherEntry.voucher_date)).all()
        return [{"date": str(x.voucher_date), "inflow": float(x.inflow), "outflow": float(x.outflow)} for x in rows]
    raise ValidationError("Unknown report")


@api.get("/reports/<report>")
@company_required
def report(report):
    items = report_data(report)
    return {"report": report, "items": items}


@api.get("/reports/<report>/excel")
@company_required
def report_excel(report):
    items = report_data(report)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = report[:31]
    if items:
        headers = list(items[0].keys())
        sheet.append(headers)
        for item in items:
            sheet.append([item.get(key) for key in headers])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=f"{report}.xlsx")


@api.get("/dashboard")
@company_required
def dashboard():
    cid = g.company_id
    return {
        "sales_total": float(Session.scalar(select(func.coalesce(func.sum(Sale.total), 0)).where(Sale.company_id == cid))),
        "purchase_total": float(Session.scalar(select(func.coalesce(func.sum(Purchase.total), 0)).where(Purchase.company_id == cid))),
        "receivables": float(Session.scalar(select(func.coalesce(func.sum(Customer.outstanding_balance), 0)).where(Customer.company_id == cid))),
        "payables": float(Session.scalar(select(func.coalesce(func.sum(Supplier.outstanding_balance), 0)).where(Supplier.company_id == cid))),
        "stock_value": float(Session.scalar(select(func.coalesce(func.sum(StockItem.quantity * StockItem.purchase_price), 0)).where(StockItem.company_id == cid))),
        "low_stock": Session.scalar(select(func.count(StockItem.id)).where(StockItem.company_id == cid, StockItem.quantity <= StockItem.reorder_level)),
    }


@api.get("/gst-records")
@company_required
def gst_records():
    rows = Session.scalars(select(GSTRecord).where(
        GSTRecord.company_id == g.company_id
    ).order_by(GSTRecord.record_date.desc(), GSTRecord.id.desc())).all()
    input_tax = sum(float(x.gst_amount) for x in rows if x.record_type == "INPUT")
    output_tax = sum(float(x.gst_amount) for x in rows if x.record_type == "OUTPUT")
    return {"items": [x.to_dict() for x in rows], "input_tax": input_tax,
            "output_tax": output_tax, "net_payable": output_tax - input_tax}


@api.get("/banking")
@company_required
def banking():
    rows = Session.execute(select(
        Ledger.id, Ledger.name,
        (Ledger.opening_balance + func.coalesce(func.sum(VoucherEntry.debit - VoucherEntry.credit), 0)).label("balance")
    ).outerjoin(VoucherEntry, VoucherEntry.ledger_id == Ledger.id).where(
        Ledger.company_id == g.company_id, Ledger.ledger_type.in_(("bank", "cash"))
    ).group_by(Ledger.id)).all()
    return {"items": [{"id": x.id, "name": x.name, "balance": float(x.balance)} for x in rows]}


@api.get("/audit-logs")
@company_required
def audit_logs():
    rows = Session.scalars(select(AuditLog).where(
        AuditLog.company_id == g.company_id
    ).order_by(AuditLog.id.desc()).limit(500)).all()
    return {"items": [x.to_dict() for x in rows]}
