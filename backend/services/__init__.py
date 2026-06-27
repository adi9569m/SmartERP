from datetime import date
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select

from database import Session
from models import (
    Company, Customer, GSTRecord, InventoryTransaction, Invoice, Ledger, Purchase,
    Sale, StockItem, Supplier, VoucherEntry
)
from schemas import ValidationError, positive, require


def next_number(model, company_id, prefix):
    count = Session.scalar(select(func.count(model.id)).where(model.company_id == company_id)) or 0
    return f"{prefix}-{date.today().year}-{count + 1:05d}"


def create_trade(kind, company_id, payload):
    party_key = "customer_id" if kind == "sale" else "supplier_id"
    party_model = Customer if kind == "sale" else Supplier
    model = Sale if kind == "sale" else Purchase
    prefix = "SAL" if kind == "sale" else "PUR"
    require(payload, party_key, "items")
    if not payload["items"]:
        raise ValidationError("At least one item is required")
    party = Session.get(party_model, int(payload[party_key]))
    if not party or party.company_id != company_id:
        raise ValidationError(f"Invalid {party_key}")

    subtotal = Decimal("0")
    gst_amount = Decimal("0")
    prepared = []
    for line in payload["items"]:
        require(line, "item_id", "quantity")
        item = Session.get(StockItem, int(line["item_id"]))
        if not item or item.company_id != company_id:
            raise ValidationError("Invalid stock item")
        quantity = positive(line["quantity"], "quantity")
        price = positive(
            line.get("unit_price", item.selling_price if kind == "sale" else item.purchase_price),
            "unit_price",
        )
        if kind == "sale" and item.quantity - item.reserved_stock < quantity:
            raise ValidationError(f"Insufficient available stock for {item.name}")
        taxable = quantity * price
        tax = taxable * item.gst_percent / Decimal("100")
        subtotal += taxable
        gst_amount += tax
        prepared.append((item, quantity, price, tax))

    number = next_number(model, company_id, prefix)
    trade = model(
        company_id=company_id, voucher_number=number, voucher_date=payload.get("voucher_date", date.today()),
        subtotal=subtotal, gst_amount=gst_amount, total=subtotal + gst_amount,
        notes=payload.get("notes", ""), **{party_key: party.id}
    )
    Session.add(trade)
    Session.flush()
    direction = Decimal("-1") if kind == "sale" else Decimal("1")
    for item, quantity, price, tax in prepared:
        item.quantity += direction * quantity
        Session.add(InventoryTransaction(
            company_id=company_id, item_id=item.id, transaction_type="STOCK_OUT" if kind == "sale" else "STOCK_IN",
            quantity=direction * quantity, unit_price=price, gst_percent=item.gst_percent,
            reference_type=kind, reference_id=trade.id, notes=payload.get("notes", "")
        ))
        Session.add(GSTRecord(
            company_id=company_id, record_type="OUTPUT" if kind == "sale" else "INPUT",
            reference_id=trade.id, taxable_amount=quantity * price, gst_percent=item.gst_percent,
            gst_amount=tax
        ))
    party.outstanding_balance += trade.total
    if party.ledger_id:
        Session.add(VoucherEntry(
            company_id=company_id, voucher_type=kind.upper(), voucher_number=number,
            ledger_id=party.ledger_id, debit=trade.total if kind == "sale" else 0,
            credit=trade.total if kind == "purchase" else 0, reference_type=kind,
            reference_id=trade.id, narration=payload.get("notes", "")
        ))
    result = trade.to_dict()
    if kind == "sale":
        invoice = Invoice(
            company_id=company_id, invoice_number=next_number(Invoice, company_id, "INV"),
            sale_id=trade.id, subtotal=subtotal, gst_amount=gst_amount, total=trade.total
        )
        Session.add(invoice)
        Session.flush()
        result["invoice"] = invoice.to_dict()
    return result


def invoice_pdf(invoice_id, company_id):
    invoice = Session.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company_id:
        raise ValidationError("Invoice not found")
    sale = Session.get(Sale, invoice.sale_id)
    company = Session.get(Company, company_id)
    customer = Session.get(Customer, sale.customer_id)
    lines = Session.scalars(select(InventoryTransaction).where(
        InventoryTransaction.reference_type == "sale",
        InventoryTransaction.reference_id == sale.id
    )).all()
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(company.name, styles["Title"]),
        Paragraph(f"{company.address}<br/>GSTIN: {company.gst_number}", styles["Normal"]),
        Spacer(1, 8*mm),
        Paragraph(f"<b>TAX INVOICE {invoice.invoice_number}</b>", styles["Heading2"]),
        Paragraph(f"Date: {invoice.invoice_date.isoformat()}<br/>Bill To: {customer.name}<br/>GSTIN: {customer.gst}", styles["Normal"]),
        Spacer(1, 5*mm),
    ]
    data = [["Item", "Qty", "Rate", "GST %", "Amount"]]
    for line in lines:
        item = Session.get(StockItem, line.item_id)
        amount = abs(line.quantity) * line.unit_price
        data.append([item.name, f"{abs(line.quantity):.3f}", f"{line.unit_price:.2f}", f"{line.gst_percent:.2f}", f"{amount:.2f}"])
    data.extend([
        ["", "", "", "Subtotal", f"{invoice.subtotal:.2f}"],
        ["", "", "", "GST", f"{invoice.gst_amount:.2f}"],
        ["", "", "", "Total", f"{invoice.total:.2f}"],
    ])
    table = Table(data, colWidths=[65*mm, 22*mm, 25*mm, 22*mm, 30*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    doc.build(story)
    output.seek(0)
    return output
