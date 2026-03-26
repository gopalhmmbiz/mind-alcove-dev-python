from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, DateTime, Text, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class LLMCall(Base):
    """
    Direct tally of every individual LLM interaction within Mind Alcove.
    """
    __tablename__ = "llm_calls_vthree"

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Identifiers
    request_id: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    # Context
    feature: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(100))

    # Input prompt
    input_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Token Metrics
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    status: Mapped[str] = mapped_column(String(20))  # "success" or "failed"
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<LLMCall(user={self.user_id}, tokens={self.total_tokens})>"
