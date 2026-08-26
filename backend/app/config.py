from typing import List, Union, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Strictly PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sarathyv:sushmidha@localhost:5432/meet"
    )
    JWT_SECRET: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # LiveKit Cloud
    LIVEKIT_URL: str = Field(default="wss://meet-2sf31hea.livekit.cloud")
    LIVEKIT_API_KEY: str = Field(default="APIJoWp2TkqDsHB")
    LIVEKIT_API_SECRET: str = Field(default="TbsvKml49HCV2qdf6fpqV6yGPfGdBqsBnDRH7miOsDmA")

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = Field(
        default="800819344034-i90ama37vntilhbhp9v111ok1fu80gup.apps.googleusercontent.com"
    )
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(
        default="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"
    )
    GOOGLE_REDIRECT_URI: Optional[str] = Field(
        default="http://localhost:8000/api/v1/auth/google/callback"
    )

    # SMTP (Gmail) for Email OTP verification
    SMTP_HOST: Optional[str] = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = Field(default="sarathy01062005@gmail.com")
    SMTP_PASSWORD: Optional[str] = Field(default="hixgwyehzbarnkac")
    SMTP_FROM_EMAIL: Optional[str] = Field(default="sarathy01062005@gmail.com")

    # CORS Origins
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,https://frontend-seven-theta-86.vercel.app,https://frontend-q9uk0z0p4-sarathys-projects-d5b7e797.vercel.app"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
