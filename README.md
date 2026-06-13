# Health Twin AI — Backend API

Health Twin AI creates a personalized digital twin of every patient, detects health deterioration before symptoms become obvious, and shows how today's choices change tomorrow's health.

---

## Setup

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/Blizzy-sus/HealthTwin.git
cd HealthTwin

# Create and activate a virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your real Anthropic API key

# Seed demo data
python seed_data.py

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Swagger UI docs at `http://127.0.0.1:8000/docs`.

---

## API Reference

### Health Twin Engine

#### `POST /twin/users` — Create a user profile

**Request body:**
```json
{
  "id": "optional-custom-id",
  "name": "Ramesh Kumar",
  "age": 60
}
```

**Response:** `UserResponse`
```json
{
  "id": "demo-user-001",
  "name": "Ramesh Kumar",
  "age": 60
}
```

---

#### `GET /twin/users/{user_id}` — Get user profile

**Response:** `UserResponse` (same shape as above)

---

#### `POST /twin/metrics/log` — Log a daily health metric

**Request body:**
```json
{
  "user_id": "demo-user-001",
  "metric_name": "bp_systolic",
  "value": 125,
  "recorded_date": "2026-06-10"
}
```

Valid `metric_name` values: `bp_systolic`, `bp_diastolic`, `sugar`, `weight`, `steps`

**Response:** `MetricResponse`
```json
{
  "id": "auto-generated-uuid",
  "user_id": "demo-user-001",
  "metric_name": "bp_systolic",
  "value": 125.0,
  "recorded_date": "2026-06-10"
}
```

---

#### `GET /twin/{user_id}/status` — Get twin status (baselines + alerts)

**Response:** `TwinStatus`
```json
{
  "user_id": "demo-user-001",
  "user_name": "Ramesh Kumar",
  "baselines": [
    {
      "metric_name": "bp_systolic",
      "average": 124.17,
      "latest": 130.0,
      "data_points": 18
    }
  ],
  "trend_alerts": [
    {
      "metric_name": "bp_systolic",
      "direction": "rising",
      "consecutive_days": 5,
      "deviation_pct": 4.7,
      "message": "bp_systolic has been above your personal average for 5 consecutive days..."
    }
  ],
  "deviation_summary": "Attention needed: bp_systolic is rising."
}
```

---

#### `POST /twin/family/link` — Link a family member to a guardian

**Request body:**
```json
{
  "guardian_id": "demo-guardian-001",
  "member_id": "demo-user-001"
}
```

---

### Medical Report Translator

#### `POST /reports/upload` — Upload and translate a medical report

**Request:** Multipart form upload with a `file` field (PDF, PNG, JPEG, WebP, or GIF)

**Response:** `ReportTranslation`
```json
{
  "values": [
    {
      "name": "HbA1c",
      "value": "7.9%",
      "plain_english": "This measures your average blood sugar over 3 months. 7.9% is higher than ideal.",
      "status": "above_range"
    }
  ],
  "summary": "Overall, your report shows elevated blood sugar levels..."
}
```

> ⚡ **AI-powered:** This endpoint calls Claude to extract and explain lab values.

---

### Silent Disease Radar

#### `POST /symptoms/analyze` — Analyze symptoms for risk patterns

**Request body:**
```json
{
  "symptoms": "frequent urination at night, increased thirst, occasional blurry vision"
}
```

**Response:** `SymptomAnalysisResponse`
```json
{
  "analysis": [
    {
      "pattern": "Type 2 Diabetes Risk",
      "resembles": "Frequent urination, increased thirst, and blurry vision are classic symptoms...",
      "recommended_test": "Fasting Blood Glucose + HbA1c",
      "urgency": "soon"
    }
  ],
  "disclaimer": "This is not a medical diagnosis. Consult a doctor."
}
```

> ⚡ **AI-powered:** This endpoint calls Claude to identify risk patterns.

---

### Future Me Simulator

#### `POST /simulator/forecast` — Generate health scenario projections

**Request body:**
```json
{
  "user_id": "demo-user-001",
  "lifestyle_changes": {
    "walk_minutes": 30,
    "weight_loss_kg": 5
  }
}
```

**Response:** `ForecastResponse`
```json
{
  "user_id": "demo-user-001",
  "current_age": 60,
  "scenario_a": {
    "label": "Current Path",
    "projected_risks": {
      "hypertension": 45,
      "type_2_diabetes": 30,
      "cardiovascular_event": 20
    },
    "health_age_estimate": 68,
    "description": "Without changes, your rising blood pressure trend suggests..."
  },
  "scenario_b": {
    "label": "With Lifestyle Changes",
    "projected_risks": {
      "hypertension": 25,
      "type_2_diabetes": 15,
      "cardiovascular_event": 10
    },
    "health_age_estimate": 58,
    "description": "With 30 minutes of daily walking and 5kg weight loss..."
  },
  "disclaimer": "This is a simulation, not a medical prediction."
}
```

> ⚡ **AI-powered:** This endpoint calls Claude to generate scenario projections.

---

### Family Guardian

#### `GET /family/{guardian_id}/dashboard` — Family health dashboard

**Response:** `FamilyDashboard`
```json
{
  "guardian_id": "demo-guardian-001",
  "members": [
    {
      "name": "Ramesh Kumar",
      "status": "yellow",
      "reason": "bp_systolic has been above your personal average for 5 consecutive days..."
    }
  ]
}
```

Status values: `green` (no alerts), `yellow` (1 alert), `red` (2+ alerts). No raw health numbers are exposed.

---

## Demo Flow

Follow these steps to demo Health Twin AI to judges:

1. **Seed demo data:**
   ```bash
   python seed_data.py
   ```
   Prints: `Demo data seeded successfully.`

2. **Start the server:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Open Swagger UI:** Navigate to `http://127.0.0.1:8000/docs`

4. **Check twin status:** `GET /twin/demo-user-001/status`
   - Shows BP trending upward (118 → 130 over 18 days)
   - Trend alert fires for `bp_systolic` — the product catches what a single reading misses

5. **Upload a medical report:** `POST /reports/upload` with any lab report image
   - Returns plain-English explanations a 60-year-old can understand

6. **Analyze symptoms:** `POST /symptoms/analyze`
   - Input: `"frequent urination at night, increased thirst, occasional blurry vision"`
   - Returns risk patterns with recommended tests and mandatory disclaimer

7. **Simulate future health:** `POST /simulator/forecast`
   - Input: `{ "user_id": "demo-user-001", "lifestyle_changes": { "walk_minutes": 30, "weight_loss_kg": 5 } }`
   - Shows Scenario A (current path) vs Scenario B (with changes) — the "aha" moment

8. **Family dashboard:** `GET /family/demo-guardian-001/dashboard`
   - Shows Ramesh Kumar as `yellow` status — his daughter Priya sees the alert without seeing raw numbers

---

## Tech Stack

- **Python 3.11+** — language
- **FastAPI** — async web framework
- **SQLAlchemy** — ORM with SQLite backend
- **SQLite** — zero-config database (no external DB needed)
- **Anthropic API** (`claude-sonnet-4-6`) — AI-powered report translation, symptom analysis, and health simulation
- **Pydantic v2** — request/response validation and serialization

---

## Next Steps

The frontend (React/TypeScript) will be built separately via Google Stitch and will connect to these backend endpoints. See `handoff.md` for the complete API contract and integration guide for the frontend developer.
