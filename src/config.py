import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    class Config:
        env_file = '.env'

    WEBDRIVER: str = os.getenv("WEBDRIVER")
    LOAD_STRATEGY: str = os.getenv("LOAD_STRATEGY")
    WINDOW_SIZE: str = os.getenv("WINDOW_SIZE")
    DISABLE_CACHE: bool = os.getenv("DISABLE_CACHE")
    NO_SANDBOX: bool = os.getenv("NO_SANDBOX")
    DISABLE_DEV_SHM_USAGE: bool = os.getenv("DISABLE_DEV_SHM_USAGE")
    HEADLESS: bool = os.getenv("HEADLESS")
    DISABLE_BLINK_FEATURES: str = os.getenv("DISABLE_BLINK_FEATURES")
    USER_AGENT: str = os.getenv("USER_AGENT")


settings = Settings()
