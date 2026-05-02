# pydantic_settings is a library that reads .env file automatically
# and gives us a nice Python object to access values
from pydantic_settings import BaseSettings

# BaseSettings = a special class that reads from .env file
class Settings(BaseSettings):
    # each line below = one variable from .env file
    # Python will automatically match the name and put the value here

    postgres_url: str        # str means this must be a text value
    mongo_url: str
    mongo_db: str
    redis_url: str
    kafka_bootstrap_servers: str
    kafka_topic: str

    # these have default values if not in .env
    app_host: str = "0.0.0.0"
    app_port: int = 8000           # int means this must be a number
    rate_limit_per_second: int = 10000
    debounce_window_seconds: int = 10
    debounce_threshold: int = 100

    class Config:
        env_file = ".env"  # read from this file

# create ONE settings object — everyone imports this same object
# this is called the Singleton pattern — one shared instance
settings = Settings()

# HOW TO USE IN OTHER FILES:
# from config.settings import settings
# print(settings.postgres_url)  → "postgresql://ims_user:ims_pass@..."