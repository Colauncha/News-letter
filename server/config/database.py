from pymongo import server_api, MongoClient

from server.config.app_config import app_config

client: MongoClient = None
    
def create_client():
    global client
    try:
        client = MongoClient(
            app_config.DB.URL,
            server_api=server_api.ServerApi(
                version="1",
                strict=True,
                deprecation_errors=True
            ),
            connect=True,
        )
        return client
    except Exception as e:
        raise Exception(f"Failed to connect to MongoDB: {e}")

def get_db ():
    global client
    if client is None:
        create_client()
    return client[app_config.DB.NAME]

def close_mongo_connection():
    print("Closing MongoDB connection...")
    client.close()
