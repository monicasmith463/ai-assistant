import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False)

    # Required fields first
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(50))  # multiple_choice, short_answer, true_false
    correct_answer: Mapped[str] = mapped_column(Text)

    # Fields with defaults
    options: Mapped[str | None] = mapped_column(Text, default=None)  # JSON string for multiple choice
    explanation: Mapped[str | None] = mapped_column(Text, default=None)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy, medium, hard
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(default_factory=uuid_pkg.uuid4, primary_key=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Foreign keys (set during creation, so init=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), index=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, init=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="questions", init=False)
