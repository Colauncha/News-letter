from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    URL: str = ""
    NAME: str =""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

class AppConfig(BaseSettings):
    app_name: str = "News Letter and Tracking App"
    version: str = "1.0.0"
    ENV: str = "development"
    debug: bool = False if ENV == "development" else True
    DB: DatabaseConfig
    JWT_SECRET_KEY: str
    CORS_ORIGINS: list[str] = [
            "http://localhost:5173", "http://localhost:5174",
            "https://biddius.com", "https://www.biddius.com",
            "https://frontend-fixserv.vercel.app",
        ] if ENV == "development" else [
            "https://biddius.com", "https://www.biddius.com",
            "https://frontend-fixserv.vercel.app"
        ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

app_config = AppConfig(DB=DatabaseConfig())
