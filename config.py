from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    SLACK_BOT_TOKEN: str
    SLACK_CHANNEL_ID: str
    LINKEDIN_EMAIL: str
    LINKEDIN_PASSWORD: str
    
    class Config:
        env_file = ".env"

settings = Settings()
