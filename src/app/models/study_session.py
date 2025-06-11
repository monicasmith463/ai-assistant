import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class StudySession(Base):
    __tablename__ = "study_session"

    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False)

    # Required fields first
    session_name: Mapped[str] = mapped_column(String(200))
    total_questions: Mapped[int] = mapped_column(Integer)

    # Fields with defaults
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    score_percentage: Mapped[float | None] = mapped_column(Float, default=None)
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    answers: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string of user answers
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(default_factory=uuid_pkg.uuid4, primary_key=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Foreign keys (set during creation, so init=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), index=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, init=False)
