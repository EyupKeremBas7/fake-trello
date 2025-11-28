import uuid
from typing import List, TYPE_CHECKING # TYPE_CHECKING ekledik
from sqlmodel import Field, Relationship, SQLModel
from app.models.enums import Visibility

if TYPE_CHECKING:
    from app.models.workspaces import Workspace
    from app.models.lists import BoardList
    from app.models.users import User

class BoardBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    visibility: Visibility = Field(default=Visibility.WORKSPACE)
    background_image: str | None = Field(default=None)

# Create
class BoardCreate(BoardBase):
    workspace_id: uuid.UUID

# Update
class BoardUpdate(BoardBase):
    name: str | None = Field(default=None, max_length=100)
    visibility: Visibility | None = None
    background_image: str | None = None

# Database Model
class Board(BoardBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE")
    owner_id: uuid.UUID = Field(foreign_key="user.id") 
    
    # İlişkilerde tırnak işareti kullanmaya devam et

    workspace: "Workspace" = Relationship(back_populates="boards")
    lists: List["BoardList"] = Relationship(back_populates="board", cascade_delete=True) 
    owner: "User" = Relationship(back_populates="boards") 

# Public Return
class BoardPublic(BoardBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    owner_id: uuid.UUID

class BoardsPublic(SQLModel):
    data: list[BoardPublic]
    count: int