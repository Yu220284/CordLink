from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    SLACK_BOT_TOKEN: str
    SLACK_CHANNEL_ID: str
    EXPANDI_API_KEY: str
    EXPANDI_API_URL: str = "https://api.expandi.io/v1"
    
    class Config:
        env_file = ".env"

settings = Settings()
