# Health Twin AI

Your health, but as a digital twin. We built this because my grandfather had a BP spike that went unnoticed for weeks — by the time anyone caught it, things had gotten serious. Health Twin watches the trends so you don't have to.

## What it does

- **Digital Twin**: Tracks daily health metrics (BP, sugar, weight, steps) and builds a personal baseline. When something drifts off, it flags it — even if each individual reading looks "fine."
- **Report Translator**: Upload a lab report (PDF/image) and get back plain-English explanations. No more Googling "what does HbA1c 7.9% mean."
- **Symptom Checker**: Describe what you're feeling, get matched to possible risk patterns with recommended tests.
- **Future Me**: "What happens if I keep going like this?" vs "What if I walk 30 min/day and lose 5kg?" — side-by-side projections.
- **Family Dashboard**: Lets family members (like a daughter keeping tabs on her dad) see a traffic-light status without exposing raw health data.

## Getting started

You'll need Python 3.11+ and an Anthropic API key.

```bash
git clone https://github.com/Priyessh-Kumar/HealthTwin.git
cd HealthTwin

python -m venv .venv
.\.venv\Scripts\activate   # on Windows
# source .venv/bin/activate  # on Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# open .env and paste your Anthropic key

python seed_data.py        # loads demo patient data
uvicorn main:app --reload  # starts at http://127.0.0.1:8000
```

Hit up `http://127.0.0.1:8000/docs` for the Swagger UI — you can test everything from there.

## API endpoints

### Twin engine
| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/twin/users` | Create a user profile |
| GET | `/twin/users/{user_id}` | Fetch a user |
| POST | `/twin/metrics/log` | Log a health metric (bp_systolic, bp_diastolic, sugar, weight, steps) |
| GET | `/twin/{user_id}/status` | Get baselines, trend alerts, and deviation summary |

### Reports & analysis
| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/reports/upload` | Upload a lab report image/PDF → get plain-English breakdown |
| POST | `/symptoms/analyze` | Describe symptoms → get risk pattern matches |
| POST | `/simulator/forecast` | Generate "current path" vs "with changes" health projections |

### Family
| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/twin/family/link` | Link a family member to a guardian |
| GET | `/family/{guardian_id}/dashboard` | Traffic-light dashboard (green/yellow/red) |

## How to demo it

1. Run `python seed_data.py` — this creates a demo patient (Ramesh, 60yo) with 18 days of BP data that gradually trends upward
2. Start the server with `uvicorn main:app --reload`
3. Open Swagger at `/docs`
4. Try `GET /twin/demo-user-001/status` — you'll see the twin caught a rising BP trend that individual readings wouldn't flag
5. Upload any lab report to `/reports/upload` — watch it translate medical jargon
6. Hit `/simulator/forecast` with some lifestyle changes — the before/after comparison is the "aha" moment
7. Check `/family/demo-guardian-001/dashboard` — Ramesh shows as "yellow" (his daughter sees the alert, not his raw numbers)

## Built with

- **FastAPI** + **SQLAlchemy** + **SQLite** (zero-config, no external DB setup)
- **Claude** (claude-sonnet-4-6 via Anthropic API) for report translation, symptom analysis, and health projections
- **Pydantic v2** for validation
