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
            self.collection.update_one({"_id": key}, {"$inc": {"nonunique_count": 1}})
            return {"nonunique_count": exist["nonunique_count"] + 1}
        else:
            self.collection.insert_one({"_id": key, "nonunique_count": 1})
            return {"nonunique_count": 1}

    def get_visitor_count(self) -> int:
        """Get the total visitor count."""
        key = f'{self.name}_{datetime.now().strftime("%Y-%m-%d")}'
        doc = self.collection.find_one({"_id": key})
        return doc["count"] if doc else 0

    def get_visitor_count_range(self, start_date: datetime, end_date: datetime) -> dict[str, int]:
        """Get the total visitor count within a date range."""
        start_key = f'{self.name}_{start_date.strftime("%Y-%m-%d")}'
        end_key = f'{self.name}_{end_date.strftime("%Y-%m-%d")}'
        
        cursor = self.collection.find({"_id": {"$gte": start_key, "$lte": end_key}})
        unique = {}
        non_unique = {}
        for doc in cursor:
            date = doc["_id"].split("_")[-1]
            unique[date] = doc.get("count", 0)
            non_unique[date] = doc.get("nonunique_count", 0)

        return {
            "unique": unique,
            "non_unique": non_unique,
            "app_name": self.name,
            "total_unique_count": sum(unique.values()),
            "total_nonunique_count": sum(non_unique.values()),
        }

    def get_non_unique_visitor_count(self) -> int:
        """Get the total visitor count."""
        key = f'{self.name}_{datetime.now().strftime("%Y-%m-%d")}'
        doc = self.collection.find_one({"_id": key})
        return doc["nonunique_count"] if doc else 0

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
