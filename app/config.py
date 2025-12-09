from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    notion_token: str
    database_id: str
    notion_version: str = "2022-06-28"

    class Config:
        env_file = ".env"


settings = Settings()
