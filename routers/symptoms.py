"""
Silent Disease Radar router.

Analyzes free-text symptoms via Claude to identify potential risk patterns.
Always includes a medical disclaimer — this is NOT a diagnosis tool.
"""

from __future__ import annotations

import json

from fastapi import APIRouter

from models.schemas import SymptomAnalysisRequest, SymptomAnalysisResponse
from services.claude_client import call_claude

router = APIRouter(prefix="/symptoms", tags=["Silent Disease Radar"])

SYMPTOM_SYSTEM_PROMPT = """\
You are a health risk pattern identifier. The user describes symptoms they have
been experiencing. Your job:

1. Identify potential risk patterns these symptoms MAY resemble.
2. For each pattern, suggest what medical test could confirm or rule it out.
3. You are NOT diagnosing. Frame every item as "pattern resembles X risk,
   recommended test: Y".
4. Be compassionate — the user may be a worried 60-year-old.

Return ONLY valid JSON with this schema (no markdown, no commentary):
[
  {
    "pattern": "Name of the risk pattern",
    "resembles": "Brief explanation of why these symptoms resemble this pattern",
    "recommended_test": "Specific test name",
    "urgency": "routine | soon | urgent"
  }
]
"""


@router.post("/analyze", response_model=SymptomAnalysisResponse)
def analyze_symptoms(payload: SymptomAnalysisRequest):
    """
    Analyze free-text symptoms for potential risk patterns.

    Returns identified patterns with recommended tests. Every response
    includes the mandatory disclaimer: "This is not a medical diagnosis.
    Consult a doctor."
    """
    raw = call_claude(
        system_prompt=SYMPTOM_SYSTEM_PROMPT,
        user_message=f"I have been experiencing the following symptoms:\n\n{payload.symptoms}",
    )

    analysis = _parse_analysis(raw)

    return SymptomAnalysisResponse(
        analysis=analysis,
        disclaimer="This is not a medical diagnosis. Consult a doctor.",
    )


def _parse_analysis(raw: str) -> list[dict]:
    """Parse Claude's JSON response, handling markdown fences."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [{"pattern": "Unable to parse", "raw_response": raw[:500]}]
