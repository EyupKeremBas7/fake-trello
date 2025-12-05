from sqlmodel import SQLModel,Field,Relationship
from datetime import datetime
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.lists import BoardList 

class CardBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None)
    position: float = Field(default=65535.0)
    due_date: datetime | None = None
    is_archived: bool = False
    cover_image: str | None = None

# Create
class CardCreate(CardBase):
    list_id: uuid.UUID

# Update
class CardUpdate(CardBase):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    position: float | None = None 
    list_id: uuid.UUID | None = None 
    due_date: datetime | None = None
    is_archived: bool | None = None
    cover_image: str | None = None

# Database Model
class Card(CardBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    list_id: uuid.UUID = Field(foreign_key="board_list.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # İlişkiler
    list: "BoardList" = Relationship(back_populates="cards")


# Public Return
class CardPublic(CardBase):
    id: uuid.UUID
    list_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class CardsPublic(SQLModel):
    data: list[CardPublic]
    count: int