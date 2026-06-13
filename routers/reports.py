"""
Medical Report Translator router.

Accepts PDF or image uploads, extracts lab values via Claude, and returns
structured plain-English explanations.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import ReportTranslation
from services.report_parser import parse_report_image, parse_report_pdf

router = APIRouter(prefix="/reports", tags=["Medical Report Translator"])

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
ALLOWED_PDF_TYPE = "application/pdf"


@router.post("/upload", response_model=ReportTranslation)
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a medical report (PDF or image) and get plain-English lab value explanations.

    Returns structured JSON with each lab value, its plain-English meaning,
    and whether it's normal, above range, or below range.
    """
    if not file.content_type:
        raise HTTPException(status_code=400, detail="File content type is required")

    content_type = file.content_type.lower()
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if content_type in ALLOWED_IMAGE_TYPES:
        result = parse_report_image(file_bytes, media_type=content_type)
    elif content_type == ALLOWED_PDF_TYPE:
        result = parse_report_pdf(file_bytes)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Upload a PDF or image (PNG, JPEG, WebP, GIF).",
        )

    return ReportTranslation(
        values=result.get("values", []),
        summary=result.get("summary", "No summary available."),
    )
