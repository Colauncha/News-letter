import csv
from io import StringIO
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

    def sub_count(self) -> int:
        return self.collection.count_documents({})

    def get_by_id(self, subscriber_id: str) -> Optional[SubscriberRead]:
        if not ObjectId.is_valid(subscriber_id):
            return None
        doc = self.collection.find_one({"_id": ObjectId(subscriber_id)})
        return SubscriberRead(**doc) if doc else None
    
    def get_by_attr(self, attr: dict[str, Any]) -> Optional[SubscriberRead]:
        doc = self.collection.find_one(attr)
        return SubscriberRead(**doc) if doc else None

    def list(
        self,
        filters: dict[str, Any] = None,
        limit: int = 50,
        skip: int = 0
    ) -> PaginatedResponse[SubscriberRead]:
        filters = filters or {}

        total = self.collection.count_documents(filters)

        cursor = self.collection.find(filters).skip(skip).limit(limit)
        docs = cursor.to_list(length=limit)

        return PaginatedResponse[SubscriberRead](
            total=total,
            skip=skip,
            limit=limit,
            pages=(total + limit - 1) // limit,  # ceiling division
            items=[SubscriberRead(**doc) for doc in docs],
        )

    def exists(self, attr: dict[str, Any]) -> bool:
        return self.collection.find_one(attr) is not None

    def create(self, document: SubscriberCreate) -> SubscriberRead:
        doc_dict = document.model_dump()
        exists = self.exists({"email": doc_dict["email"]})
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscriber with this email already exists."
            )
        result = self.collection.insert_one(doc_dict)
        if result:
            return SubscriberRead(id=str(result.inserted_id), **doc_dict)
        raise HTTPException(
            detail="Failed to create subscriber.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def update(self, subscriber_id: str, updates: SubscriberUpdate) -> bool:
        if not ObjectId.is_valid(subscriber_id):
            return False
        result = self.collection.update_one(
            {"_id": ObjectId(subscriber_id)},
            {"$set": updates.model_dump(exclude_unset=True)}
        )
        return result.modified_count > 0

    def delete(self, subscriber_id: str) -> bool:
        if not ObjectId.is_valid(subscriber_id):
            return False
        result = self.collection.delete_one({"_id": ObjectId(subscriber_id)})
        return result.deleted_count > 0

    def _create_csv_content(self, items: List[SubscriberRead]) -> str:
        """
        Convert database items to CSV string content
        
        Args:
            items: List of database records
            
        Returns:
            str: CSV content as string
        """
        # Create StringIO object to write CSV in memory
        output = StringIO()
        
        # Define CSV headers
        headers = ['id', 'email', 'updates', 'marketing', 'announcements', 'newsletters', 'seasonal']
        
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # Process each SubscriberRead item
        for item in items:
            campaigns = item.campaigns  # Direct access since it's a Pydantic model
            
            row = {
                'id': str(item.id),  # Using the model's id field
                'email': item.email,
                'updates': campaigns.updates if campaigns else False,
                'marketing': campaigns.marketing if campaigns else False,
                'announcements': campaigns.announcements if campaigns else False,
                'newsletters': campaigns.newsletters if campaigns else False,
                'seasonal': campaigns.seasonal if campaigns else False
            }
            
            writer.writerow(row)
        
        # Get CSV content and reset pointer
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
