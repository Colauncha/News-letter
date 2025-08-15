import jwt
import hashlib

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from ..config.app_config import app_config
from ..schemas import PaginatedResponse
from ..schemas.app_client_schema import (
    AppClientCreate,
    AppClientRead,
    AppClientUpdate
)
from ..dependencies import get_app_client_model, verify_bearer_token
from ..collections.appClient import AppClient

router = APIRouter(prefix="/app-client", tags=["AppClient"])


@router.post("/", response_model=dict[str, str | int | datetime], status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    payload: AppClientCreate,
    app_client_model: AppClient = Depends(get_app_client_model)
):
    if await app_client_model.exists({"email": payload.email}):
        raise HTTPException(status_code=400, detail="App already exists")
    data = await app_client_model.create(payload)
    return data


@router.get("/{app_client_id}", response_model=AppClientRead)
async def get_app_client(
    app_client_id: str,
    app_client_model: AppClient = Depends(get_app_client_model)
):
    app_client = await app_client_model.get_by_id(app_client_id)
    if not app_client:
        raise HTTPException(status_code=404, detail="App Client not found")
    return app_client


@router.get("/", response_model=PaginatedResponse[AppClientRead])
async def list_app_clients(
    skip: int = 0,
    limit: int = 50,
    app_client_model: AppClient = Depends(get_app_client_model)
):
    print("Listing app clients with skip:", skip, "and limit:", limit)
    return await app_client_model.list(skip=skip, limit=limit)


@router.put("/{app_client_id}", response_model=bool)
async def update_app_client(
    app_client_id: str,
    payload: AppClientUpdate,
    app_client_model: AppClient = Depends(get_app_client_model),
    app_client=Depends(verify_bearer_token)
):
    if app_client["client_data"]["id"] != app_client_id:
        raise HTTPException(status_code=403, detail="You can only update your own App Client")
    payload.updated_at = payload.updated_at or datetime.now(timezone.utc)
    updated = await app_client_model.update(app_client_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="App Client not found or no changes made")
    return updated


@router.delete("/{app_client_id}", response_model=bool)
async def delete_app_client(
    app_client_id: str,
    app_client_model: AppClient = Depends(get_app_client_model),
    app_client=Depends(verify_bearer_token)
):
    if app_client["client_data"]["id"] != app_client_id:
        raise HTTPException(status_code=403, detail="You can only delete your own App Client")
    deleted = await app_client_model.delete(app_client_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="App Client not found")
    return deleted


@router.post("/refresh-token")
async def refresh_token(
    auth_data=Depends(verify_bearer_token),
    app_client_model: AppClient = Depends(get_app_client_model)
):
    """Generate a new token for the client"""
    api_key = auth_data["api_key"]
    client_data = auth_data["client_data"]
    
    # Generate new token with extended expiry
    new_payload = {
        "api_key": api_key,
        "client_id": client_data["id"],
        "client_name": client_data["name"],
        "collection_name": client_data["collection_name"],
        "exp": datetime.now(timezone.utc) + timedelta(days=365),
        "iat": datetime.now(timezone.utc),
        "iss": "your-api-service",
        "sub": api_key
    }
    
    # Get client salt from database
    client = await app_client_model.collection.find_one({"API_KEY": api_key})
    jwt_secret = hashlib.sha256(f"{app_config.JWT_SECRET_KEY}:{client['client_salt']}".encode()).hexdigest()
    
    new_token = jwt.encode(new_payload, jwt_secret, algorithm="HS256")
    
    return {
        "access_token": new_token,
        "token_type": "Bearer",
        "expires_in": 31536000,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    }
