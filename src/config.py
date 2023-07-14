from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ip: str = "127.0.0.1"
    port: int = 7123


settings = Settings()
