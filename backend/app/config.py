from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    max_rows: int = 500
    statement_timeout_ms: int = 5000
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
