from sqlmodel import SQLModel,Field,Relationship
import uuid
from typing import List,TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.boards import Board
    from app.models.cards import Card 


# Shared Properties
class ListBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    position: float = Field(default=65535.0) 

# Create
class ListCreate(ListBase):
    board_id: uuid.UUID


class ListUpdate(ListBase):
    name: str | None = Field(default=None, max_length=100)
    position: float | None = None 


class BoardList(ListBase, table=True):
    __tablename__ = "board_list"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    board_id: uuid.UUID = Field(foreign_key="board.id", ondelete="CASCADE")
    
    # İlişkiler
    board: "Board" = Relationship(back_populates="lists")
    cards: List["Card"] = Relationship(back_populates="list", cascade_delete=True)

# Public Return
class ListPublic(ListBase):
    id: uuid.UUID
    board_id: uuid.UUID

class ListsPublic(SQLModel):
    data: list[ListPublic]
    count: int