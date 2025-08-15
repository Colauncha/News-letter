from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas import PaginatedResponse
from ..schemas.subcribers_schema import SubscriberCreate, SubscriberRead, SubscriberUpdate
from ..dependencies import get_subscriber_model
from ..collections.subscribers import Subscriber

router = APIRouter(prefix="/subscribers", tags=["Subscribers"])


@router.post("/", response_model=dict[str, SubscriberRead | str], status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    payload: SubscriberCreate,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    if await subscriber_model.exists({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Subscriber already exists")
    new = await subscriber_model.create(payload)
    return {
        "message": "Subscribed successfully",
        "data": new
    }


@router.get("/{subscriber_id}", response_model=SubscriberRead)
async def get_subscriber(
    subscriber_id: str,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    subscriber = await subscriber_model.get_by_id(subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return subscriber


@router.get("/", response_model=PaginatedResponse[SubscriberRead])
async def list_subscribers(
    skip: int = 0,
    limit: int = 50,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    return await subscriber_model.list(skip=skip, limit=limit)


@router.put("/{subscriber_id}", response_model=bool)
async def update_subscriber(
    subscriber_id: str,
    payload: SubscriberUpdate,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    payload.updated_at = payload.updated_at or datetime.now(timezone.utc)
    updated = await subscriber_model.update(subscriber_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Subscriber not found or no changes made")
    return updated


@router.delete("/{subscriber_id}", response_model=bool)
async def delete_subscriber(
    subscriber_id: str,
    subscriber_model: Subscriber = Depends(get_subscriber_model)
):
    deleted = await subscriber_model.delete(subscriber_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return deleted
