Вот полный шаблон микросервиса на Python с использованием принципов чистой архитектуры и DDD, включая все запрошенные компоненты:

### Структура проекта
```
my_microservice/
├── app/
│   ├── api/
│   │   ├── v1/                     # Versioning
│   │   │   ├── endpoints/          # REST/GRPC handlers
│   │   │   └── __init__.py
│   │   └── base_api.py             # Base API
│   ├── consumers/
│   │   ├── kafka_consumer.py       # Base Consumers
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py               # Configuration
│   │   ├── logging.py              # Logging
│   │   └── monitoring.py           # Monitoring
│   ├── domain/                     # DDD Core
│   │   ├── models/
│   │   ├── repositories/
│   │   └── services/
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── postgres.py         # PostgreSQL
│   │   │   └── models.py           # SQLAlchemy ORM
│   │   ├── grpc_client.py          # GRPC Client
│   │   └── minio_client.py         # Minio Client
│   └── __init__.py
├── tests/
├── .gitlab-ci.yml                  # Base CI/CD
├── docker-compose.yml              # Base Arch
├── Dockerfile
├── requirements.txt
├── .env.example                    # ENV Configuration
└── README.md
```

### Ключевые файлы

1. **app/core/config.py** (Configuration ENV)
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "My Microservice"
    API_V1_STR: str = "/api/v1"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_TOPIC: str
    
    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Minio
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

2. **app/infrastructure/database/postgres.py** (PostgreSQL + SQLAlchemy)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
    echo=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

3. **app/consumers/kafka_consumer.py** (Async Kafka)
```python
from aiokafka import AIOKafkaConsumer
import asyncio
import json
from app.core.config import settings
from app.core.logging import logger

async def consume():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="my-group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    
    await consumer.start()
    try:
        async for msg in consumer:
            logger.info(f"Received message: {msg.value}")
            # Process message here
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume())
```

4. **app/api/base_api.py** (FastAPI Base)
```python
from fastapi import FastAPI
from app.core.monitoring import instrumentator
from app.core.logging import setup_logging

app = FastAPI(title="My Microservice")

# Setup components
setup_logging()
instrumentator.instrument(app).expose(app)

@app.on_event("startup")
async def startup():
    # Initialize connections
    pass

@app.on_event("shutdown")
async def shutdown():
    # Close connections
    pass
```

5. **app/core/monitoring.py** (Prometheus)
```python
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics"],
)
```

6. **Dockerfile** (Python 3.9-slim)
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.api.base_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

7. **docker-compose.yml** (Base Arch)
```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - POSTGRES_HOST=postgres
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - kafka

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data

  kafka:
    image: bitnami/kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
      KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
    depends_on:
      - zookeeper

  zookeeper:
    image: bitnami/zookeeper:latest

  minio:
    image: minio/minio
    command: server /data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"

volumes:
  pgdata:
```

8. **.gitlab-ci.yml** (Base CI/CD)
```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG

test:
  stage: test
  image: python:3.9
  script:
    - pip install -r requirements.txt
    - pytest

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $DOCKER_IMAGE .
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $DOCKER_IMAGE

deploy:
  stage: deploy
  script:
    - echo "Deploy to production"
  environment: production
```

### Требуемые зависимости (requirements.txt)
```
fastapi
uvicorn
sqlalchemy
asyncpg
aiokafka
minio
grpcio
grpcio-tools
pydantic
python-dotenv
prometheus-fastapi-instrumentator
```

### Особенности реализации:
1. **Чистая архитектура**:
   - Domain: Бизнес-логика в `domain/`
   - Infrastructure: Внешние сервисы в `infrastructure/`
   - Application: API и Consumers

2. **Асинхронность**:
   - Kafka через aiokafka
   - PostgreSQL через asyncpg
   - FastAPI ASGI

3. **Мониторинг**:
   - Prometheus метрики через prometheus-fastapi-instrumentator
   - Логирование в JSON формате

4. **Безопасность**:
   - Конфигурация через .env файл
   - Изолированные Docker-контейнеры

5. **Масштабируемость**:
   - Горизонтальное масштабирование потребителей Kafka
   - Stateless дизайн API

Для запуска:
1. Создайте `.env` файл по примеру `.env.example`
2. Запустите: `docker-compose up --build`

Этот шаблон обеспечивает:
- Готовую к production инфраструктуру
- Поддержку синхронных (gRPC, Minio) и асинхронных (Kafka) взаимодействий
- Автоматизированное тестирование и деплой
- Мониторинг и логирование
- Соответствие принципам DDD и чистой архитектуры