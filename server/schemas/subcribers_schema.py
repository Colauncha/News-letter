from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from ..utils import PyObjectId


class CampaignObj(BaseModel):
    updates: bool = True
    marketing: bool = True
    announcements: bool = True
    newsletters: bool = True
    seasonal: bool = True


class SubscriberCreate(BaseModel):
    email: EmailStr
    campaigns: CampaignObj = Field(default_factory=CampaignObj)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class SubscriberRead(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    campaigns: CampaignObj = Field(default_factory=CampaignObj)
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class SubscriberUpdate(BaseModel):
    """Schema for partial updates."""
    email: Optional[EmailStr] = None
    campaigns: Optional[CampaignObj] = None
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
