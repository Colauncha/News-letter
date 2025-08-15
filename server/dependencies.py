import traceback
from typing import Optional
from fastapi import Depends, HTTPException, Header, status

from server.collections.subscribers import Subscriber


# async def get_app_client_model() -> AppClient:
#     return AppClient()

def get_app_client_model():
    try:
        from server.collections.appClient import AppClient
        return AppClient()
    except Exception as e:
        print("ERROR in get_app_client_model:", e)
        traceback.print_exc()
        raise


async def verify_bearer_token(
    authorization: Optional[str] = Header(None, description="Bearer token"),
    client_service=Depends(get_app_client_model)  # Your service injection
):
    """FastAPI dependency to verify Bearer JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required"
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.split(" ")[1]
    return await client_service.verify_jwt_token(token)

async def get_subscriber_model(auth_data=Depends(verify_bearer_token)) -> Subscriber:
    if not auth_data:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    client = auth_data.get("client_data")
    if not client:
        raise HTTPException(status_code=401, detail="Invalid client data in token")
    collection_name = client.get("collection_name")
    if not collection_name:
        raise HTTPException(status_code=400, detail="Collection name not found in client data")
    return Subscriber(collection_name)
