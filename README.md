# SmartERP

SmartERP is a PostgreSQL-backed billing, inventory and accounting system built with Flask, SQLAlchemy, Next.js, React, Tailwind CSS, ShadCN-style UI components, TanStack Table, ReportLab and OpenPyXL.

## Project structure

```text
backend/
  app.py                 Flask application factory
  auth/                  Password authentication
  config/                Environment configuration
  controllers/           Reusable CRUD controllers
  database/              SQLAlchemy engine and sessions
  models/                Database models
  routes/                REST API routes
  services/              Trade posting and invoice services
  schemas/               Request validation
  middleware/            JWT, company scope and audit helpers
  migrations/            Alembic migration
  tests/                 Core unit tests
frontend/
  app/                    Next.js routes
  components/             ERP layout, forms and TanStack tables
  lib/                    REST API client
```

The additional requested backend module folders (`inventory`, `accounting`, `reports`, and `utils`) are present as Python packages; their HTTP behavior is exposed through the organized routes and transaction services.

## Database schema

| Table | Purpose |
|---|---|
| `users` | Login identities and password hashes |
| `companies` | Company profile, GST and financial year |
| `groups` | Assets, liabilities, income and expense grouping |
| `ledgers` | Customer, supplier, expense, income, bank and cash ledgers |
| `stock_groups`, `units`, `stock_items` | Inventory masters and stock state |
| `customers`, `suppliers` | Party masters and outstanding balances |
| `purchases`, `sales` | Posted trade vouchers |
| `invoices` | Auto-numbered sales invoices |
| `voucher_entries` | Double-entry accounting postings |
| `inventory_transactions` | Stock movement and sale/purchase lines |
| `gst_records` | Input and output GST entries |
| `audit_logs` | User and entity activity |

All company-owned records carry `company_id`. Money uses fixed precision numeric columns. Posting a purchase or sale, its stock movements, GST records, outstanding balance, ledger entry and invoice occur in one database transaction.

## Installation

Requirements: Python 3.12+, Node.js, npm, and PostgreSQL.

Create a PostgreSQL database named `smarterp`, then:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` and `JWT_SECRET_KEY` in your environment (the application deliberately has no extra dotenv dependency), then migrate and run:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/smarterp"
$env:JWT_SECRET_KEY="replace-with-a-long-random-secret"
alembic upgrade head
python app.py
```

In another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`, register the first user, create a company, and select it.

## Docker / Render

The backend Dockerfile is ready for Render. Build it from `backend/`:

```powershell
docker build -t smarterp-backend .
docker run -p 5000:5000 -e DATABASE_URL="postgresql+psycopg://..." -e JWT_SECRET_KEY="..." smarterp-backend
```

Run `alembic upgrade head` against the Render PostgreSQL database before starting the web service.

## REST API

Authentication uses `Authorization: Bearer <JWT>`. Company-scoped routes additionally require `X-Company-ID`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | Authentication |
| GET | `/api/auth/me` | Current user |
| GET, POST | `/api/companies` | List/create companies |
| PUT, DELETE | `/api/companies/:id` | Edit/delete company |
| GET, POST | `/api/groups`, `/api/ledgers` | Accounting masters |
| GET, POST | `/api/stock-groups`, `/api/stock-items`, `/api/units` | Stock masters |
| GET, POST | `/api/customers`, `/api/suppliers` | Party masters |
| PUT, DELETE | `/api/{master}/:id` | Edit/delete any master |
| GET, POST | `/api/purchases`, `/api/sales` | List/post trade vouchers |
| GET | `/api/invoices`, `/api/invoices/:id` | Invoice list/detail |
| GET | `/api/invoices/:id/pdf` | ReportLab PDF invoice |
| GET, POST | `/api/inventory/transactions` | Stock movement and adjustment |
| POST | `/api/vouchers` | Payment, receipt and journal posting |
| GET | `/api/parties/:type/:id/statement` | Customer/supplier ledger statement |
| GET | `/api/dashboard` | Dashboard totals |
| GET | `/api/banking`, `/api/gst-records`, `/api/audit-logs` | Operational modules |
| GET | `/api/reports/:report` | Report data |
| GET | `/api/reports/:report/excel` | OpenPyXL export |

Reports: `balance-sheet`, `profit-loss`, `trial-balance`, `cash-flow`, `stock-summary`, `low-stock`, `daily-sales`, `monthly-sales`, `purchase-register`, and `supplier-summary`.

## Keyboard shortcuts

`F5` Payment · `F6` Receipt · `F7` Journal · `F8` Sales · `F9` Purchase · `Ctrl+B` Invoices · `Ctrl+I` Inventory · `Ctrl+K` Search · `Ctrl+H` Dashboard · `Esc` Previous screen.

## Tests

```powershell
cd backend
python -m unittest discover -s tests
```
