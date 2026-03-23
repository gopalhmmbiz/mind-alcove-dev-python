from sqlalchemy import (
    BigInteger,
    String,
    Text,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base


class UserProfile(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    goal: Mapped[str] = mapped_column(String(255), nullable=True)
    base_mood: Mapped[str] = mapped_column(String(100), nullable=True)

    journal_profile: Mapped[str] = mapped_column(Text, nullable=True)
    activity_suggestion_profile: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now()
    )
