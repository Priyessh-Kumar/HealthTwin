"""
Future Me Simulator router — the hackathon differentiator.

Uses current twin baseline + Claude to generate two-scenario projections:
Scenario A (current path) vs Scenario B (with lifestyle changes).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import (
    ForecastRequest,
    ForecastResponse,
    MetricORM,
    Scenario,
    UserORM,
)
from services.baseline_engine import compute_baselines
from services.claude_client import call_claude

router = APIRouter(prefix="/simulator", tags=["Future Me Simulator"])

FORECAST_SYSTEM_PROMPT = """\
You are a health scenario simulator. Given a patient's current health baselines
and proposed lifestyle changes, generate two scenarios:

Scenario A — "Current Path": What happens if they continue their current lifestyle
for 5 years. Estimate risk percentages for key conditions and a "health age"
(biological age estimate).

Scenario B — "With Changes": What happens if they adopt the proposed lifestyle
changes. Show improved risk percentages and health age.

Be compassionate but honest. This is a SIMULATION, not a prediction.

Return ONLY valid JSON (no markdown, no commentary):
{
  "scenario_a": {
    "label": "Current Path",
    "projected_risks": {
      "hypertension": 45,
      "type_2_diabetes": 30,
      "cardiovascular_event": 20
    },
    "health_age_estimate": 68,
    "description": "One-paragraph description of this scenario"
  },
  "scenario_b": {
    "label": "With Lifestyle Changes",
    "projected_risks": {
      "hypertension": 25,
      "type_2_diabetes": 15,
      "cardiovascular_event": 10
    },
    "health_age_estimate": 58,
    "description": "One-paragraph description of this scenario"
  }
}
"""


@router.post("/forecast", response_model=ForecastResponse)
def forecast(payload: ForecastRequest, db: Session = Depends(get_db)):
    """
    Generate health scenario projections based on current twin baseline
    and optional lifestyle changes.

    Returns two scenarios: current path vs. with changes. All output is
    clearly labeled as simulation, not prediction.
    """
    user = db.query(UserORM).filter(UserORM.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Gather current baselines
    all_metrics = (
        db.query(MetricORM)
        .filter(MetricORM.user_id == payload.user_id)
        .order_by(MetricORM.recorded_date.asc())
        .all()
    )
    metrics_by_name: dict[str, list[float]] = {}
    for m in all_metrics:
        metrics_by_name.setdefault(m.metric_name, []).append(m.value)

    baselines = compute_baselines(metrics_by_name)
    baselines_str = "\n".join(
        f"- {b.metric_name}: average={b.average}, latest={b.latest}" for b in baselines
    )

    changes_str = json.dumps(payload.lifestyle_changes or {})

    user_message = (
        f"Patient: {user.name}, Age: {user.age}\n\n"
        f"Current health baselines:\n{baselines_str}\n\n"
        f"Proposed lifestyle changes: {changes_str}\n\n"
        f"Generate two scenarios (current path vs with changes) for the next 5 years."
    )

    raw = call_claude(
        system_prompt=FORECAST_SYSTEM_PROMPT,
        user_message=user_message,
        max_tokens=1500,
    )

    parsed = _parse_forecast(raw, user.age)

    return ForecastResponse(
        user_id=payload.user_id,
        current_age=user.age,
        scenario_a=parsed["scenario_a"],
        scenario_b=parsed["scenario_b"],
        disclaimer="This is a simulation, not a medical prediction.",
    )


def _parse_forecast(raw: str, current_age: int) -> dict:
    """Parse Claude's forecast JSON, with a fallback."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        data = json.loads(text)
        return {
            "scenario_a": Scenario(**data["scenario_a"]),
            "scenario_b": Scenario(**data["scenario_b"]),
        }
    except (json.JSONDecodeError, KeyError):
        return {
            "scenario_a": Scenario(
                label="Current Path",
                projected_risks={"parse_error": 0},
                health_age_estimate=current_age + 5,
                description=f"Could not generate detailed scenario. Raw: {raw[:300]}",
            ),
            "scenario_b": Scenario(
                label="With Lifestyle Changes",
                projected_risks={"parse_error": 0},
                health_age_estimate=current_age,
                description="Could not generate detailed scenario.",
            ),
        }
