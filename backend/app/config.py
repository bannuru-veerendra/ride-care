import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env"),
        extra="ignore",
    )

    APP_ENV: str
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    FRONTEND_URL: str = "http://localhost:5173"
    EMAIL_FROM: str = "RideCare <noreply@example.com>"
    # Prefer Brevo (HTTPS) on Render free — outbound SMTP ports are blocked there.
    # Free plan: verify a sender email (e.g. your Gmail) in Brevo; no domain required.
    BREVO_API_KEY: str = ""
    # SMTP fallback (local / paid hosts that allow 587). Example: smtp.gmail.com
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_STARTTLS: bool = True
    # Shared secret for POST /internal/reminder-digests (GitHub Actions cron). Empty = disabled.
    REMINDER_CRON_SECRET: str = ""
    DATABASE_URL: str
    REDIS_URL: str
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_STORAGE_BUCKET: str
    ALLOWED_ORIGINS: str = "http://localhost:5173"


settings = Settings()
