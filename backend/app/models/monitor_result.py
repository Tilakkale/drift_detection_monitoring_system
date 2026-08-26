from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from datetime import datetime
from backend.app.database.connection import Base

class MonitorResult(Base):

    __tablename__ = "monitor_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    machine_id = Column(
        Integer,
        nullable=False
    )

    row_count = Column(
        Integer,
        nullable=False
    )

    anomaly_count = Column(
        Integer,
        nullable=False
    )

    anomaly_fraction = Column(
        Float,
        nullable=False
    )

    drifted_feature_count = Column(
        Integer,
        nullable=False
    )

    drift_details = Column(
        Text,
        nullable=True
    )

    severity = Column(
        String(20),
        nullable=False,
        default="low"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
