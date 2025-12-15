from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class SoftDeleteMixin(SQLModel):
    """Mixin for soft delete functionality."""
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: datetime | None = Field(default=None)
    deleted_by: str | None = Field(default=None)

    def soft_delete(self, deleted_by: str | None = None) -> None:
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
