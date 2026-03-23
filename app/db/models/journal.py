from sqlalchemy import (
    BigInteger,
    Text,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base


class JournalPost(Base):
    __tablename__ = "journal_posts"

    jp_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger
    )

    post_questions: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    post: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now()
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )
