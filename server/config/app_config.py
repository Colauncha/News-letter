from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    URL: str = ""
    NAME: str =""

    model_config = {
        "env_prefix": "DATABASE_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

class AppConfig(BaseSettings):
    app_name: str = "News Letter and Tracking App"
    debug: bool = False
    version: str = "1.0.0"
    ENV: str = "development"
    DB: DatabaseConfig
    JWT_SECRET_KEY: str

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

app_config = AppConfig(DB=DatabaseConfig())
