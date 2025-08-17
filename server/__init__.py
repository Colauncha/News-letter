import json
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .config.app_config import app_config
from .config.database import create_client
from .routes.appClient import router as app_router
from .routes.subscriber import router as sub_router


def create_app():
    create_client()

    app = FastAPI(
        title=app_config.app_name,
        debug=app_config.debug,
        version=app_config.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        description="API for News Letter and Tracking App",
        # lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def display_request_info(request: Request, call_next):
        print(f"Request: {request.headers} {request.client}")
        response = await call_next(request)
        print(f"Response: {response.status_code}")
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        print("Unhandled error:", exc)
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": str(exc)})


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
