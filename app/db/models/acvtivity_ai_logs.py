from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    func,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base
from datetime import date, datetime


class ActivityAiLog(Base):
    __tablename__ = "activity_ai_logs_vthree"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Note: Use datetime.date for the 'date' column to match the 'date' SQL type
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # JSON columns for suggested and performed activities
    suggested: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        default=None
    )

    performed: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Define the unique constraint for user_id and date
    __table_args__ = (
        UniqueConstraint(
            "user_id", "date",
            name="activity_ai_logs_vthree_user_id_date_unique"
        ),
    )
