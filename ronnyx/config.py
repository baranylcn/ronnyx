from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    notion_token: str | None = Field(default=None, alias="NOTION_TOKEN")
    notion_version: str | None = Field(default=None, alias="NOTION_VERSION")
    database_id: str | None = Field(default=None, alias="DATABASE_ID")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    ronnyx_base_url: str = Field(default="http://localhost:8000/api/chat", alias="RONNYX_BASE_URL")

    llm_model: str = Field(default="gpt-4o", alias="LLM_MODEL")

    class Config:
        env_file = ".env"


settings = Settings()
