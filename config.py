from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    #get default values so, will later integrate a different way of keeping .env variables a secret using GitHub Actions Secrets 
    
    TOPIC_DEFAULT : str = "home/#"

    #region BaseSettings for DB
    # db_port = int = 5433
    #endregion

    #region BaseSettings for Mqtt
    # mqtt_host = str = "localhost"
    # mqtt_port = int = 1883

    #endregion

    #region BaseSettings for Redis
    # redis_port = int = 6739
    #endregion

