from typing import Optional

from pydantic import BaseModel
from pydantic import Field as PydanticField


class ItemCreate(BaseModel):
    name: str = PydanticField(..., min_length=2, max_length=100)
    category: str
    color: str
    season: str
    notes: str = ""


class ItemUpdate(BaseModel):
    name: Optional[str] = PydanticField(None, min_length=2, max_length=100)
    category: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    notes: Optional[str] = None
