"""
Pydantic schemas (API contracts) and SQLAlchemy ORM models for Health Twin AI.

Every request/response shape used by the API is defined here so the frontend
team can read this single file to understand the full data contract.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from models.database import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM models
# ---------------------------------------------------------------------------

class UserORM(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    metrics = relationship("MetricORM", back_populates="user", cascade="all, delete-orphan")
    family_links = relationship("FamilyLinkORM", foreign_keys="FamilyLinkORM.member_id", back_populates="member")


class MetricORM(Base):
    __tablename__ = "metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # bp_systolic, bp_diastolic, sugar, weight, steps
    value = Column(Float, nullable=False)
    recorded_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserORM", back_populates="metrics")


class FamilyLinkORM(Base):
    __tablename__ = "family_links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    guardian_id = Column(String, ForeignKey("users.id"), nullable=False)
    member_id = Column(String, ForeignKey("users.id"), nullable=False)

    member = relationship("UserORM", foreign_keys=[member_id], back_populates="family_links")


# ---------------------------------------------------------------------------
# Pydantic request schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Create a new user profile with personal baselines."""
    id: Optional[str] = Field(None, description="Custom user ID; auto-generated if omitted")
    name: str = Field(..., description="User's display name")
    age: int = Field(..., ge=0, le=150, description="User's age in years")


class MetricLog(BaseModel):
    """Log a daily health metric."""
    user_id: str
    metric_name: str = Field(
        ...,
        description="One of: bp_systolic, bp_diastolic, sugar, weight, steps",
    )
    value: float
    recorded_date: date


class SymptomAnalysisRequest(BaseModel):
    """Free-text symptom list for the Silent Disease Radar."""
    symptoms: str = Field(..., description="Free-text description of symptoms")


class ForecastRequest(BaseModel):
    """Lifestyle change scenario for the Future Me Simulator."""
    user_id: str
    lifestyle_changes: Optional[dict] = Field(
        None,
        description='e.g. {"walk_minutes": 30, "weight_loss_kg": 5}',
    )


class FamilyLinkCreate(BaseModel):
    """Link a family member to a guardian."""
    guardian_id: str
    member_id: str


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    id: str
    name: str
    age: int

    model_config = {"from_attributes": True}


class MetricResponse(BaseModel):
    id: str
    user_id: str
    metric_name: str
    value: float
    recorded_date: date

    model_config = {"from_attributes": True}


class BaselineEntry(BaseModel):
    metric_name: str
    average: float
    latest: float
    data_points: int


class TrendAlert(BaseModel):
    metric_name: str
    direction: str  # "rising" | "falling"
    consecutive_days: int
    deviation_pct: float
    message: str


class TwinStatus(BaseModel):
    user_id: str
    user_name: str
    baselines: list[BaselineEntry]
    trend_alerts: list[TrendAlert]
    deviation_summary: str


class LabValue(BaseModel):
    name: str
    value: str
    plain_english: str
    status: str  # "normal" | "above_range" | "below_range"


class ReportTranslation(BaseModel):
    values: list[LabValue]
    summary: str


class SymptomAnalysisResponse(BaseModel):
    analysis: list[dict]
    disclaimer: str = "This is not a medical diagnosis. Consult a doctor."


class Scenario(BaseModel):
    label: str
    projected_risks: dict
    health_age_estimate: int
    description: str


class ForecastResponse(BaseModel):
    user_id: str
    current_age: int
    scenario_a: Scenario  # Current path
    scenario_b: Scenario  # With lifestyle changes
    disclaimer: str = "This is a simulation, not a medical prediction."


class FamilyMemberStatus(BaseModel):
    name: str
    status: str  # "green" | "yellow" | "red"
    reason: str


class FamilyDashboard(BaseModel):
    guardian_id: str
    members: list[FamilyMemberStatus]
