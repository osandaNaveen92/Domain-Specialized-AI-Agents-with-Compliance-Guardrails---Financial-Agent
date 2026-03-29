# Financial Close GenAI Agent

AI-assisted financial close system with reconciliation, framework controls (SOX/IFRS/GAAP), risk scoring, governance gates, approval workflow, and audit reporting.

## What This Project Does

- Reconciles bank vs GL transactions with confidence scoring
- Generates journal entries for unmatched items
- Applies controls from a configurable control catalog
- Calculates risk score and priority per entry
- Enforces governance rules:
  - Materiality gates (L1/L2/L3)
  - Human review routing (`PENDING_REVIEW`)
  - Segregation of Duties (preparer cannot self-approve)
- Maintains approval/rejection history with actor + timestamp
- Generates control-based audit report PDF
- Supports close lifecycle endpoints:
  - `/close/initiate`
  - `/close/status`
  - `/close/package`

## Tech Stack

- Python + FastAPI
- MongoDB (local)
- OpenAI API (for explanation generation path)
- HTML dashboard (`/dashboard`)

## Project Structure

```text
financial-close-agent/
├── app.py
├── dashboard.html
├── config/
│   ├── db.py
│   └── control_catalog.json
├── data/
│   ├── sample_bank.csv
│   └── sample_gl.csv
├── modules/
│   ├── controller.py
│   ├── control_evaluator.py
│   ├── control_loader.py
│   ├── explainer.py
│   ├── journal.py
│   ├── report.py
│   └── rule_engine.py
├── src/
│   ├── data/database.py
│   ├── governance/engine.py
│   ├── models/schemas.py
│   └── services/close_service.py
└── utils/
    ├── matcher.py
    └── parser.py
```

## Prerequisites

- Python 3.11+
- MongoDB running on `mongodb://localhost:27017/`
- OpenAI API key in `.env` (optional but recommended)

## Setup

```powershell
cd c:\Users\Acer\financial-close-agent
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

If you don’t have `requirements.txt`, install the core dependencies:

```powershell
pip install fastapi uvicorn pymongo python-dotenv pandas rapidfuzz reportlab openai
```

## Environment

Create `.env`:

```env
OPENAI_API_KEY=your_openai_key_here
```

## Run the App

```powershell
.\venv\Scripts\activate
uvicorn app:app --reload
```

Open:

- Dashboard: `http://127.0.0.1:8000/dashboard`
- Swagger Docs: `http://127.0.0.1:8000/docs`

## Dashboard Flow

1. Enter close period (example: `2026-03`)
2. Click **Initiate Close**
3. Click **Run Reconciliation**
4. Review pending items/risk/controls
5. Approve or reject entries with approver name
6. Generate audit report

## Main API Endpoints

### Data

- `GET /transactions`
- `GET /matches`
- `GET /journal`

### Close Workflow

- `POST /close/initiate?period=YYYY-MM`
- `GET /close/status?period=YYYY-MM`
- `GET /close/package?period=YYYY-MM`
- `POST /run-close?period=YYYY-MM` (period optional)

### Governance and Reviews

- `GET /reviews/pending`
- `GET /governance/dashboard`

### Approval Workflow

- `POST /approve/{entry_id}?approver=Name`
- `POST /reject/{entry_id}?approver=Name`

### Reporting

- `GET /generate-report`

## Notes

- If dashboard shows no records, run `Initiate Close` and then `Run Reconciliation`.
- `run-close` processes sample CSV files from `/data`.
- Explanations use OpenAI when applicable and configured.
