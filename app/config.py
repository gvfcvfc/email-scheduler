from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    SECRET_KEY: str

    EMAIL_USER: str
    EMAIL_PASS: str

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    DATABASE_URL: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    SESSION_SECRET: str

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID: str
    APP_URL: str = "http://127.0.0.1:8000"

    FRONTEND_URL: str = "http://127.0.0.1:8501"
    

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    
settings = Settings()