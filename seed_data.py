"""
Demo seed script for Health Twin AI.

Creates a demo user with 18 days of health data that tells the product's
hero story: BP trending upward from 118 → 130 while other metrics stay stable.

Usage:
    python seed_data.py
"""

import sys
import os
from datetime import date, timedelta

# Ensure the project root is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db, SessionLocal
from models.schemas import UserORM, MetricORM, FamilyLinkORM


def seed():
    """Seed the database with demo data."""
    init_db()
    db = SessionLocal()

    # Clean up any existing demo data
    db.query(FamilyLinkORM).filter(
        (FamilyLinkORM.guardian_id == "demo-guardian-001") |
        (FamilyLinkORM.member_id == "demo-user-001")
    ).delete(synchronize_session=False)
    db.query(MetricORM).filter(MetricORM.user_id.in_(["demo-user-001", "demo-guardian-001"])).delete(synchronize_session=False)
    db.query(UserORM).filter(UserORM.id.in_(["demo-user-001", "demo-guardian-001"])).delete(synchronize_session=False)
    db.commit()

    # ---- Demo user (the patient) ----
    demo_user = UserORM(id="demo-user-001", name="Ramesh Kumar", age=60)
    db.add(demo_user)

    # ---- Guardian user (family member) ----
    guardian = UserORM(id="demo-guardian-001", name="Priya Kumar", age=35)
    db.add(guardian)

    # ---- Family link ----
    family_link = FamilyLinkORM(
        guardian_id="demo-guardian-001",
        member_id="demo-user-001",
    )
    db.add(family_link)

    # ---- 18 days of health metrics ----
    start_date = date.today() - timedelta(days=17)

    # BP Systolic: trending from 118 → 130 (the hero story)
    bp_values = [
        118, 119, 118, 120, 121, 122, 123, 122, 124,
        125, 126, 125, 127, 128, 128, 129, 130, 130,
    ]

    # BP Diastolic: mild upward trend
    bp_dia_values = [
        76, 77, 76, 78, 78, 79, 79, 80, 80,
        81, 81, 82, 82, 83, 83, 84, 84, 85,
    ]

    # Sugar (fasting): stable around 105
    sugar_values = [
        104, 106, 103, 105, 107, 104, 106, 105, 103,
        105, 106, 104, 107, 105, 104, 106, 105, 103,
    ]

    # Weight: stable at 74 kg
    weight_values = [
        74.0, 74.1, 73.9, 74.0, 74.2, 74.1, 74.0, 73.9, 74.0,
        74.1, 74.0, 74.2, 74.1, 74.0, 73.9, 74.0, 74.1, 74.0,
    ]

    # Steps: stable around 6000/day
    steps_values = [
        6100, 5800, 6200, 5900, 6000, 6300, 5700, 6100, 6000,
        5900, 6200, 5800, 6100, 6000, 5900, 6200, 5800, 6000,
    ]

    metrics_data = [
        ("bp_systolic", bp_values),
        ("bp_diastolic", bp_dia_values),
        ("sugar", sugar_values),
        ("weight", weight_values),
        ("steps", steps_values),
    ]

    for metric_name, values in metrics_data:
        for i, value in enumerate(values):
            metric = MetricORM(
                user_id="demo-user-001",
                metric_name=metric_name,
                value=value,
                recorded_date=start_date + timedelta(days=i),
            )
            db.add(metric)

    db.commit()
    db.close()
    print("Demo data seeded successfully.")


if __name__ == "__main__":
    seed()
