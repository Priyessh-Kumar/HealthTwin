"""
Report parser — accepts PDF or image uploads, converts to base64, and sends
to Claude for lab-value extraction and plain-English explanation.
"""

from __future__ import annotations

import base64
import json

from services.claude_client import call_claude, call_claude_with_image

REPORT_SYSTEM_PROMPT = """\
You are a medical report translator. The user has uploaded a medical lab report
(as an image or PDF page). Your job:

1. Extract every lab value you can find (name, numeric value with unit).
2. For each value, write a plain-English explanation a 60-year-old can understand.
3. Classify each as "normal", "above_range", or "below_range".

Return ONLY valid JSON — no markdown, no commentary. Use this exact schema:
{
  "values": [
    {
      "name": "HbA1c",
      "value": "7.9%",
      "plain_english": "This measures your average blood sugar over 3 months. 7.9% is higher than the ideal range (below 5.7%), which means your blood sugar has been elevated.",
      "status": "above_range"
    }
  ],
  "summary": "One-paragraph overall summary in simple language."
}
"""


def parse_report_image(file_bytes: bytes, media_type: str) -> dict:
    """
    Parse a medical report image via Claude vision.

    Args:
        file_bytes: Raw bytes of the uploaded image.
        media_type: MIME type (e.g. "image/png", "image/jpeg").

    Returns:
        Parsed JSON dict with lab values and summary.
    """
    image_b64 = base64.b64encode(file_bytes).decode("utf-8")
    raw = call_claude_with_image(
        system_prompt=REPORT_SYSTEM_PROMPT,
        user_text="Please extract and explain all lab values from this medical report.",
        image_base64=image_b64,
        media_type=media_type,
        max_tokens=2000,
    )
    return _safe_parse_json(raw)


def parse_report_pdf(file_bytes: bytes) -> dict:
    """
    Parse a PDF report by sending it as a document to Claude.

    For the hackathon MVP, we send the PDF as base64 and ask Claude
    to extract values. This works for single-page reports.

    Args:
        file_bytes: Raw bytes of the PDF.

    Returns:
        Parsed JSON dict with lab values and summary.
    """
    pdf_b64 = base64.b64encode(file_bytes).decode("utf-8")
    raw = call_claude(
        system_prompt=REPORT_SYSTEM_PROMPT,
        user_message=(
            f"The following is a base64-encoded PDF of a medical lab report:\n\n"
            f"{pdf_b64}\n\n"
            f"Please extract and explain all lab values you can identify."
        ),
        max_tokens=2000,
    )
    return _safe_parse_json(raw)


def _safe_parse_json(raw: str) -> dict:
    """Attempt to parse JSON from Claude's response, handling markdown fences."""
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "values": [],
            "summary": f"Could not parse structured data. Raw response: {raw[:500]}",
        }
