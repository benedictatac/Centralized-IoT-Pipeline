from typing import ClassVar
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra ="ignore",)

    #get default values so, will later integrate a different way of keeping .env variables a secret using GitHub Actions Secrets 
    
    topic_default : str = "home/#"

    #region BaseSettings for DB
    db_port: int = 5433
    db_user: str
    db_password: str
    db_name: str
    db_host : str = "localhost"
    #endregion

    #region BaseSettings for Mqtt
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    #endregion

    #region BaseSettings for Redis
    rds_port:int = 6379
    rds_user : str	
    rds_password : str
    rds_name : str
    rds_host : str = "localhost"
    #endregion

