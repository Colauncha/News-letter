import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse

from .config.app_config import app_config
from .config.database import create_client, close_mongo_connection
from .routes.appClient import router as app_router
from .routes.subscriber import router as sub_router


def create_app():
    # Initialize the database client
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_client()
        yield
        await close_mongo_connection()

    app = FastAPI(
        title=app_config.app_name,
        debug=app_config.debug,
        version=app_config.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        description="API for News Letter and Tracking App",
        lifespan=lifespan
    )

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs", status_code=302)

    @app.get("/health", include_in_schema=False)
    async def health_check():
        return {"status": "Running ✅"}
    
    @app.get("/version", include_in_schema=False)
    async def version():
        return {"version": app_config.version}
    
    @app.get("/info", include_in_schema=True)
    async def info():
        if app_config.ENV == "development":
            return app_config.model_dump(exclude=['JWT_SECRET_KEY'])
        else:
            return {"app_name": app_config.app_name, "version": app_config.version}
    
    # TODO: Add other routes and include them in the app
    app.include_router(app_router)
    app.include_router(sub_router)

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"], include_in_schema=False)
    async def catch_all(full_path: str, request: Request):
        return Response(json.dumps({"error": "Not Found"}), status_code=404, media_type="application/json")

    return app
