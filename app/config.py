from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    notion_token: str | None = Field(default=None, alias="NOTION_TOKEN")
    notion_version: str | None = Field(default=None, alias="NOTION_VERSION")
    database_id: str | None = Field(default=None, alias="DATABASE_ID")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    discord_bot_token: str | None = Field(default=None, alias="DISCORD_BOT_TOKEN")
    discord_guild_id: str | None = Field(default=None, alias="DISCORD_GUILD_ID")

    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")

    class Config:
        env_file = ".env"


settings = Settings()
