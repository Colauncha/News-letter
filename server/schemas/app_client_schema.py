from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from ..utils import PyObjectId


class AppClientCreate(BaseModel):
    name: str
    website: str
    email: EmailStr
    collection_name: str
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AppClientRead(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    website: str
    email: EmailStr
    collection_name: str
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)


class AppClientUpdate(BaseModel):
    """Schema for partial updates."""
    name: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
