from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from backend.app.database.connection import Base


class Alert(Base):

    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    machine_id = Column(
        Integer,
        nullable=False
    )

    alert_type = Column(
        String(50),
        nullable=False
    )

    severity = Column(
        String(20),
        nullable=False
    )

    message = Column(
        String(500),
        nullable=False
    )

    resolved = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
