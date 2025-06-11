import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base


class Document(Base):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False)

    # Required fields first
    title: Mapped[str] = mapped_column(String(200))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(10))  # pdf, pptx, docx
    file_size: Mapped[int] = mapped_column(Integer)  # in bytes

    # Fields with defaults
    content: Mapped[str | None] = mapped_column(Text, default=None)  # extracted text
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(default_factory=uuid_pkg.uuid4, primary_key=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Foreign key to user (set during creation, so init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, init=False)

    # Relationships
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="document", init=False)
