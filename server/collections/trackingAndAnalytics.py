import csv
from datetime import datetime
from io import StringIO
from bson import ObjectId
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import uuid4
from fastapi import HTTPException, status

# from ..schemas import PaginatedResponse
from ..config.database import get_db

if TYPE_CHECKING:
    from pymongo.collection import Collection


class TrackerAndAnalytics:
    collection: "Collection"

    def __init__(self, collection_name: str = "tracking_and_analytics", name: str = "default"):
        # Directly bind the collection
        self.collection = get_db()[collection_name]
        self.name = name

    def increase_visitor_count(self) -> dict[str, int]:
        """Increase the visitor count by 1."""
        key = f'{self.name}_{datetime.now().strftime("%Y-%m-%d")}'
        exist = self.collection.find_one({"_id": key})
        if exist:
            self.collection.update_one({"_id": key}, {"$inc": {"count": 1}})
            return {"count": exist["count"] + 1}
        else:
            self.collection.insert_one({"_id": key, "count": 1})
            return {"count": 1}

    def increase_non_unique_visitor_count(self) -> dict[str, int]:
        """Increase the visitor count by 1."""
        key = f'{self.name}_{datetime.now().strftime("%Y-%m-%d")}'
        exist = self.collection.find_one({"_id": key})
        if exist:
            self.collection.update_one({"_id": key}, {"$inc": {"non-unique-count": 1}})
            return {"non-unique-count": exist["non-unique-count"] + 1}
        else:
            self.collection.insert_one({"_id": key, "non-unique-count": 1})
            return {"non-unique-count": 1}


    def get_visitor_count(self) -> int:
        """Get the total visitor count."""
        key = f'{self.name}_{datetime.now().strftime("%Y-%m-%d")}'
        doc = self.collection.find_one({"_id": key})
        return doc["count"] if doc else 0

    def get_non_unique_visitor_count(self) -> int:
        """Get the total visitor count."""
        key = f'{self.name}_{datetime.now().strftime("%Y-%m-%d")}'
        doc = self.collection.find_one({"_id": key})
        return doc["non-unique-count"] if doc else 0


    def get_unique_visitors(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[str]:
        """Get unique visitors within a date range."""
        if start_date is None:
            start_date = datetime.min
        if end_date is None:
            end_date = datetime.max

        start_key = f'{self.name}_{start_date.strftime("%Y-%m-%d")}'
        end_key = f'{self.name}_{end_date.strftime("%Y-%m-%d")}'
        
        cursor = self.collection.find({"_id": {"$gte": start_key, "$lte": end_key}})
        return [doc["_id"] for doc in cursor]

    def get_unique_visitor_count(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> int:
        """Get the count of unique visitors within a date range."""
        unique_visitors = self.get_unique_visitors(start_date, end_date)
        return len(unique_visitors)
