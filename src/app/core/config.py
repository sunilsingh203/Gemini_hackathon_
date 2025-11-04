from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Resume Parser"
    API_V1_PREFIX: str = "/api/v1"

    # SQLite file DB; change to ":memory:" if you want in-memory only
    DATABASE_URL: str = "sqlite:///./app.db"

    MAX_FILE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
