import jwt
import secrets
import hashlib

from uuid import uuid4
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, List, Optional
from fastapi import HTTPException

from ..config.database import get_db, app_config
from ..schemas import PaginatedResponse
from ..schemas.app_client_schema import (
    AppClientCreate,
    AppClientRead,
    AppClientUpdate
)


if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection


class AppClient:
    collection: "AsyncIOMotorCollection"

    def __init__(self):
        # Directly bind the collection
        self.collection = get_db()["appClient"]

    async def get_by_id(self, app_client_id: str) -> Optional[AppClientRead]:
        if not app_client_id:
            return None
        doc = await self.collection.find_one({"_id": app_client_id})
        return doc if doc else None

    async def list(
        self,
        filters: dict[str, Any] = None,
        limit: int = 50,
        skip: int = 0
    ) -> PaginatedResponse[AppClientRead]:
        filters = filters or {}

        total = await self.collection.count_documents(filters)

        cursor = self.collection.find(filters).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        items = [AppClientRead(**doc) for doc in docs if doc]
        return PaginatedResponse[AppClientRead](
            total=total,
            skip=skip,
            limit=limit,
            pages=(total + limit - 1) // limit,
            items=items,
        )

    async def exists(self, attr: dict[str, Any]) -> bool:
        return await self.collection.find_one(attr) is not None

    async def update(self, app_client_id: str, updates: AppClientUpdate) -> bool:
        if not app_client_id:
            return False
        result = await self.collection.update_one(
            {"_id": app_client_id},
            {"$set": updates.model_dump(exclude_unset=True)}
        )
        return result.modified_count > 0

    async def delete(self, app_client_id: str) -> bool:
        if not app_client_id:
            return False
        result = await self.collection.delete_one({"_id": app_client_id})
        return result.deleted_count > 0

    async def create(self, document: AppClientCreate) -> dict[str, str | int | datetime]:
        """Improved create method using master secret approach"""
        doc_dict = document.model_dump()
        exists = await self.exists({"name": doc_dict["name"]})
        if exists:
            raise HTTPException(status_code=400, detail="App Client with this name already exists.")
        
        # Generate API_KEY (public identifier)
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        
        # Generate client-specific salt for JWT signing
        client_salt = secrets.token_urlsafe(32)
        
        # Prepare document for database
        doc_dict.update({
            "API_KEY": api_key,
            "client_salt": client_salt,  # Store salt for JWT secret derivation
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
            "token_expires_days": 365
        })
        
        print(f"Creating client: {doc_dict['name']} with API_KEY: {api_key}")
        result = await self.collection.insert_one(doc_dict)
        
        # Create JWT secret by combining master secret with client salt
        jwt_secret = hashlib.sha256(f"{app_config.JWT_SECRET_KEY}:{client_salt}".encode()).hexdigest()
        
        # Generate JWT token
        payload = {
            "api_key": api_key,
            "client_id": str(result.inserted_id),
            "client_name": doc_dict["name"],
            "collection_name": doc_dict["collection_name"],
            "exp": datetime.now(timezone.utc) + timedelta(days=365),
            "iat": datetime.now(timezone.utc),
            "iss": "your-api-service",
            "sub": api_key
        }
        
        access_token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        
        return {
            "id": str(result.inserted_id),
            "name": doc_dict["name"],
            "api_key": api_key,
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 31536000,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            "message": "Store the access_token securely. Use it in Authorization header as 'Bearer <token>'"
        }

    async def verify_jwt_token(self, token: str) -> dict:
        """Verify JWT token using master secret approach"""
        try:
            # First decode without verification to get the API key
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            api_key = unverified_payload.get("api_key")
            
            if not api_key:
                raise HTTPException(status_code=401, detail="Invalid token: missing API key")
            
            # Get client from database
            client = await self.collection.find_one({"API_KEY": api_key, "is_active": True})
            if not client:
                raise HTTPException(status_code=401, detail="Invalid API key or client inactive")
            
            # Recreate JWT secret using master secret and client salt
            client_salt = client["client_salt"]
            jwt_secret = hashlib.sha256(f"{app_config.JWT_SECRET_KEY}:{client_salt}".encode()).hexdigest()
            
            # Verify and decode the token
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            
            # Add client info to payload
            payload["client_data"] = {
                "id": str(client["_id"]),
                "name": client["name"],
                "website": client["website"],
                "email": client["email"],
                "collection_name": client["collection_name"]
            }
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
