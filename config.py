from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.pipeline.listener import MQTT_HOST, MQTT_PORT


class Settings(BaseSettings):

    #get default values so, will later integrate a different way of keeping .env variables a secret using GitHub Actions Secrets 
    
    TOPIC_DEFAULT : str = "home/#"

    #region BaseSettings for DB
    DB_PORT = int = 5433
    #endregion

    #region BaseSettings for Mqtt
    MQTT_HOST= str = "localhost"
    MQTT_PORT= int = 1883

    #endregion

    #region BaseSettings for Redis
    RDS_PORT= int = 6739
    #endregion

