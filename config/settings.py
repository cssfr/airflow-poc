from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str = Field(env="SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(env="SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_ANON_KEY: Optional[str] = Field(env="SUPABASE_ANON_KEY", default=None)
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = Field(env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="trading-data", env="MINIO_BUCKET")
    MINIO_USE_SSL: bool = Field(default=False, env="MINIO_USE_SSL")
    
    # Airflow Configuration
    AIRFLOW_POSTGRES_USER: str = Field(env="AIRFLOW_POSTGRES_USER")
    AIRFLOW_POSTGRES_PASSWORD: str = Field(env="AIRFLOW_POSTGRES_PASSWORD")
    AIRFLOW_POSTGRES_DB: str = Field(env="AIRFLOW_POSTGRES_DB")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()