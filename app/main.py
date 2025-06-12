from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram
import time
import logging
from pythonjsonlogger import jsonlogger
from app.core.config import Settings
from app.core.database import Database
from app.core.kafka import KafkaProducer
from app.core.minio import MinioClient

# Настройка логирования
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Инициализация приложения
app = FastAPI(title="Fault-Tolerant Microservice")
settings = Settings()

# Метрики Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Инициализация клиентов
db = Database(settings)
kafka = KafkaProducer(settings)
minio = MinioClient(settings)

@app.on_event("startup")
async def startup():
    await db.connect()
    await kafka.connect()
    await minio.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
    await kafka.disconnect()
    await minio.disconnect()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return {"status": "metrics endpoint"}

@app.get("/")
async def root():
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    with REQUEST_LATENCY.time():
        try:
            # Пример работы с базой данных
            result = await db.execute("SELECT 1")
            
            # Пример отправки сообщения в Kafka
            await kafka.send_message("test-topic", {"message": "Hello"})
            
            # Пример работы с Minio
            await minio.upload_file("test.txt", "Hello World")
            
            return {"message": "Success", "result": result}
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 