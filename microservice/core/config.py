from pydantic import BaseSettings, AnyUrl, PostgresDsn

class Settings(BaseSettings):
    # Общие настройки
    DEBUG: bool = False
    PROJECT_NAME: str = "My Microservice"
    ENVIRONMENT: str = "local"
    
    # API
    API_V1_STR: str = "/api/v1"
    GRPC_SERVER: str = "0.0.0.0:50051"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_CONSUMER_GROUP: str = "microservice-group"
    KAFKA_TOPICS: list = ["events"]
    
    # PostgreSQL
    POSTGRES_DSN: PostgresDsn = "postgresql+asyncpg://user:password@localhost:5432/db"
    POOL_SIZE: int = 20
    POOL_MAX_OVERFLOW: int = 5
    
    # Minio
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    
    # Sentry
    SENTRY_DSN: AnyUrl | None = None
    
    # Application settings
    LOG_LEVEL: str = "INFO"
    METRICS_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings() 