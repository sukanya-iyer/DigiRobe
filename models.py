from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """Data model for users"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str
    name: str
    email: str

    items: List["ClothingItem"] = Relationship(back_populates="user")


class ClothingItem(SQLModel, table=True):
    """Data model for clothing items"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    color: str
    season: str
    notes: str = ""

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="items")
