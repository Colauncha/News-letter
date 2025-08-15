from bson import ObjectId
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import uuid4
from fastapi import HTTPException, status

from ..schemas import PaginatedResponse
from ..config.database import get_db
from ..schemas.subcribers_schema import (
    SubscriberCreate,
    SubscriberRead,
    SubscriberUpdate
)

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection


class Subscriber:
    collection: "AsyncIOMotorCollection"

    def __init__(self, collection_name: str = "subscribers"):
        # Directly bind the collection
        self.collection = get_db()[collection_name]

    async def sub_count(self) -> int:
        return await self.collection.count_documents({})

    async def get_by_id(self, subscriber_id: str) -> Optional[SubscriberRead]:
        if not ObjectId.is_valid(subscriber_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(subscriber_id)})
        return SubscriberRead(**doc) if doc else None
    
    async def get_by_attr(self, attr: dict[str, Any]) -> Optional[SubscriberRead]:
        doc = await self.collection.find_one(attr)
        return SubscriberRead(**doc) if doc else None

    async def list(
        self,
        filters: dict[str, Any] = None,
        limit: int = 50,
        skip: int = 0
    ) -> PaginatedResponse[SubscriberRead]:
        filters = filters or {}

        total = await self.collection.count_documents(filters)

        cursor = self.collection.find(filters).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)

        return PaginatedResponse[SubscriberRead](
            total=total,
            skip=skip,
            limit=limit,
            pages=(total + limit - 1) // limit,  # ceiling division
            items=[SubscriberRead(**doc) for doc in docs],
        )

    async def exists(self, attr: dict[str, Any]) -> bool:
        return await self.collection.find_one(attr) is not None

    async def create(self, document: SubscriberCreate) -> SubscriberRead:
        doc_dict = document.model_dump()
        exists = await self.exists({"email": doc_dict["email"]})
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscriber with this email already exists."
            )
        result = await self.collection.insert_one(doc_dict)
        if result:
            return SubscriberRead(id=str(result.inserted_id), **doc_dict)
        raise HTTPException(
            detail="Failed to create subscriber.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    async def update(self, subscriber_id: str, updates: SubscriberUpdate) -> bool:
        if not ObjectId.is_valid(subscriber_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(subscriber_id)},
            {"$set": updates.model_dump(exclude_unset=True)}
        )
        return result.modified_count > 0

    async def delete(self, subscriber_id: str) -> bool:
        if not ObjectId.is_valid(subscriber_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(subscriber_id)})
        return result.deleted_count > 0
