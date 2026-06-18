from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_STORAGE_BUCKET: str
    FRONTEND_URL: str

    class Config:
        env_file = ".env"

settings = Settings()