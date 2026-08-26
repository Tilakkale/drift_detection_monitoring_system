from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime
)

from datetime import datetime

from backend.app.database.connection import Base


class DriftResult(Base):

    __tablename__ = "drift_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    dataset_id = Column(
        Integer,
        nullable=False
    )

    feature_name = Column(
        String(100),
        nullable=False
    )

    psi_score = Column(
        Float,
        nullable=False
    )

    drift_status = Column(
        String(50),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )