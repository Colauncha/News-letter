import asyncio
from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import server_api

from server.config.app_config import app_config

client: AsyncIOMotorClient = None
    
@lru_cache
async def create_client():
    global client
    try:
        client = AsyncIOMotorClient(
            app_config.DB.URL,
            server_api=server_api.ServerApi(
                version="1",
                strict=True,
                deprecation_errors=True
            ),
            connect=True,
        )
    except Exception as e:
        raise Exception(f"Failed to connect to MongoDB: {e}")

def get_db () -> AsyncIOMotorDatabase:
    return client[app_config.DB.NAME]

async def close_mongo_connection():
    print("Closing MongoDB connection...")
    client.close()
