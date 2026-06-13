"""
Family Guardian router.

Returns each linked family member's status as green/yellow/red based on
their twin deviation alerts — no raw numbers exposed to the guardian view.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import (
    FamilyDashboard,
    FamilyLinkORM,
    FamilyMemberStatus,
    MetricORM,
    UserORM,
)
from services.baseline_engine import detect_trends

router = APIRouter(prefix="/family", tags=["Family Guardian"])


@router.get("/{guardian_id}/dashboard", response_model=FamilyDashboard)
def family_dashboard(guardian_id: str, db: Session = Depends(get_db)):
    """
    Returns each linked family member's status as green / yellow / red.

    Status is derived from twin deviation alerts:
    - green: no trend alerts
    - yellow: 1 trend alert
    - red: 2+ trend alerts

    No raw health numbers are exposed — only traffic-light status and a reason.
    """
    guardian = db.query(UserORM).filter(UserORM.id == guardian_id).first()
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")

    links = db.query(FamilyLinkORM).filter(FamilyLinkORM.guardian_id == guardian_id).all()
    if not links:
        return FamilyDashboard(guardian_id=guardian_id, members=[])

    members: list[FamilyMemberStatus] = []
    for link in links:
        member = db.query(UserORM).filter(UserORM.id == link.member_id).first()
        if not member:
            continue

        # Get member's metrics and compute trends
        all_metrics = (
            db.query(MetricORM)
            .filter(MetricORM.user_id == member.id)
            .order_by(MetricORM.recorded_date.asc())
            .all()
        )
        metrics_by_name: dict[str, list[float]] = {}
        for m in all_metrics:
            metrics_by_name.setdefault(m.metric_name, []).append(m.value)

        alerts = detect_trends(metrics_by_name)

        if len(alerts) == 0:
            status = "green"
            reason = "All metrics are within personal normal range."
        elif len(alerts) == 1:
            status = "yellow"
            reason = alerts[0].message
        else:
            status = "red"
            reason = "; ".join(a.message for a in alerts)

        members.append(
            FamilyMemberStatus(name=member.name, status=status, reason=reason)
        )

    return FamilyDashboard(guardian_id=guardian_id, members=members)
