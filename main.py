# NOT A MEDICAL DEVICE
"""
Health Twin AI — Backend API
Creates a personalized digital twin of every patient, detects health
deterioration before symptoms become obvious, and shows how today's
choices change tomorrow's health.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import twin, reports, symptoms, simulator, family

load_dotenv()

app = FastAPI(
    title="Health Twin AI",
    description=(
        "Personalized digital health twin API. "
        "NOT A MEDICAL DEVICE — for informational purposes only."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(twin.router)
app.include_router(reports.router)
app.include_router(symptoms.router)
app.include_router(simulator.router)
app.include_router(family.router)


@app.get("/", tags=["health"])
def health_check():
    """Root health-check endpoint."""
    return {"status": "healthy", "service": "Health Twin AI"}
