"""
Health Twin Engine — the core router.

Handles user profile creation, daily metric logging, and the twin status
endpoint that returns personal baselines, trend alerts, and deviation summary.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db, init_db
from models.schemas import (
    FamilyLinkCreate,
    MetricLog,
    MetricResponse,
    TwinStatus,
    UserCreate,
    UserORM,
    MetricORM,
    FamilyLinkORM,
    UserResponse,
)
from services.baseline_engine import compute_baselines, detect_trends, deviation_summary

router = APIRouter(prefix="/twin", tags=["Health Twin Engine"])


@router.on_event("startup")
def startup():
    init_db()


@router.post("/users", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user profile."""
    user = UserORM(
        id=payload.id or None,
        name=payload.name,
        age=payload.age,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Retrieve a user profile."""
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/metrics/log", response_model=MetricResponse)
def log_metric(payload: MetricLog, db: Session = Depends(get_db)):
    """Log a daily health metric for a user."""
    user = db.query(UserORM).filter(UserORM.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    metric = MetricORM(
        user_id=payload.user_id,
        metric_name=payload.metric_name,
        value=payload.value,
        recorded_date=payload.recorded_date,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("/{user_id}/status", response_model=TwinStatus)
def get_twin_status(user_id: str, db: Session = Depends(get_db)):
    """
    Returns current baselines, trend alerts, and deviation summary for a user.

    This is the primary "digital twin" endpoint — it tells you how the user
    is doing relative to their own personal normal.
    """
    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_metrics = (
        db.query(MetricORM)
        .filter(MetricORM.user_id == user_id)
        .order_by(MetricORM.recorded_date.asc())
        .all()
    )

    # Group by metric name
    metrics_by_name: dict[str, list[float]] = {}
    for m in all_metrics:
        metrics_by_name.setdefault(m.metric_name, []).append(m.value)

    baselines = compute_baselines(metrics_by_name)
    alerts = detect_trends(metrics_by_name)
    summary = deviation_summary(alerts)

    return TwinStatus(
        user_id=user_id,
        user_name=user.name,
        baselines=baselines,
        trend_alerts=alerts,
        deviation_summary=summary,
    )


@router.post("/family/link")
def link_family_member(payload: FamilyLinkCreate, db: Session = Depends(get_db)):
    """Link a family member to a guardian for the Family Guardian dashboard."""
    # Validate both users exist
    guardian = db.query(UserORM).filter(UserORM.id == payload.guardian_id).first()
    member = db.query(UserORM).filter(UserORM.id == payload.member_id).first()
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian user not found")
    if not member:
        raise HTTPException(status_code=404, detail="Member user not found")

    link = FamilyLinkORM(
        guardian_id=payload.guardian_id,
        member_id=payload.member_id,
    )
    db.add(link)
    db.commit()
    return {"status": "linked", "guardian_id": payload.guardian_id, "member_id": payload.member_id}
