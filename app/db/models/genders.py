from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class Gender(Base):
    __tablename__ = "genders"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    gender_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    gender_logo: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    color: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
