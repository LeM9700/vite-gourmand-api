from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    postgres_url: str
    jwt_secret: str
    jwt_alg: str
    jwt_expire_minutes: int = 120

    # Configuration API
    api_title: str = "Vite & Gourmand API"
    api_version: str = "1.0.0"
    api_description: str = "API pour l'application de traiteur Vite & Gourmand"
    environment: str = "development"  # development, production, staging
    
    # Variables d'environnement
    mongo_url: str
    mongo_db: str

    # Mailgun API (remplace SMTP)
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mailgun_from: str = "Vite & Gourmand <postmaster@sandboxa202e5da33de4c73bc794850c6f43abd.mailgun.org>"

    # SMTP (optionnel, conservé pour rétro-compatibilité)
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from: str = ""

    email_confirmation_expire_hours: int = 24
    email_confirmation_secret: str = ""
    frontend_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False
    )

settings = Settings()
