from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    postgres_url: str
    jwt_secret: str
    jwt_alg: str
    jwt_expire_minutes: int=120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False
    )

settings = Settings()
