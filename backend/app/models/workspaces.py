import uuid
from sqlmodel import Field, Relationship, SQLModel
from typing import List,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.boards import Board  


class WorkspaceBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_archived: bool = False


# Create
class WorkspaceCreate(WorkspaceBase):
    pass

# Update
class WorkspaceUpdate(WorkspaceBase):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

# Database Model
class Workspace(WorkspaceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # İlişkiler
    boards: List["Board"] = Relationship(back_populates="workspace", cascade_delete=True)

# Public Return
class WorkspacePublic(WorkspaceBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime

class WorkspacesPublic(SQLModel):
    data: list[WorkspacePublic]
    count: int