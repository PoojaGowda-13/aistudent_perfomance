import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    agent_type: Mapped[str] = mapped_column(String(100))
    session_id: Mapped[str] = mapped_column(String(200))
    input_hash: Mapped[Optional[str]] = mapped_column(String(64))
    input_summary: Mapped[Optional[str]] = mapped_column(Text)
    output_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON as text
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(100))
    model_name: Mapped[Optional[str]] = mapped_column(String(100))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    hitl_required: Mapped[bool] = mapped_column(default=False)
    hitl_approved: Mapped[Optional[str]] = mapped_column(String(5), default=None)  # "true"/"false"/None
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="agent_sessions")


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_type: Mapped[str] = mapped_column(String(100))
    llm_provider: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
