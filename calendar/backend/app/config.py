from typing import List, Union, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # PostgreSQL Database URL
    DATABASE_URL: str = Field(
        default="postgresql://sarathy:rDmHrQUmrdNFS57XRxINnGZgYZUtJddD@dpg-da7ioi3m6pss73fsgpn0-a.singapore-postgres.render.com/com_2gid"
    )

    # JWT Secret (shared with Meet for SSO)
    JWT_SECRET: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Internal Service Key (shared between Calendar and Meet)
    INTERNAL_SERVICE_KEY: str = Field(
        default="sidaz_internal_secret_key_meet_calendar_2026"
    )

    # Meet Service URL (REST API)
    MEET_API_URL: str = Field(
        default="https://backend-omega-vert-20.vercel.app"
    )

    # Frontend URL for RSVP redirection
    FRONTEND_URL: str = Field(
        default="http://localhost:5174"
    )

    # CORS Allowed Origins
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,https://frontend-seven-theta-86.vercel.app,https://meridian-calendar.vercel.app"
    )

    # SMTP Configuration for Email Invitations and Reminders
    SMTP_HOST: Optional[str] = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = Field(default="sarathy01062005@gmail.com")
    SMTP_PASSWORD: Optional[str] = Field(default="hixgwyehzbarnkac")
    SMTP_FROM_EMAIL: Optional[str] = Field(default="sarathy01062005@gmail.com")
    SMTP_FROM_NAME: str = Field(default="Meridian Calendar")

    # Web Browser Push Notifications (VAPID)
    VAPID_PUBLIC_KEY: Optional[str] = Field(
        default="BNxW_example_public_vapid_key_meridian_2026"
    )
    VAPID_PRIVATE_KEY: Optional[str] = Field(
        default="example_private_vapid_key_meridian_2026"
    )
    VAPID_SUBJECT: str = Field(default="mailto:admin@sidanex.com")

    # Feature Flags
    EMAIL_INVITES_ENABLED: bool = True
    EMAIL_REMINDERS_ENABLED: bool = True
    PUSH_NOTIFICATIONS_ENABLED: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
