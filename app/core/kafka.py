from kafka import KafkaProducer
import json
from app.core.config import Settings

class KafkaProducer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.producer = None

    async def connect(self):
        self.producer = KafkaProducer(
            bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )

    async def disconnect(self):
        if self.producer:
            self.producer.close()

    async def send_message(self, topic: str, message: dict):
        if not self.producer:
            raise Exception("Kafka producer not connected")
        
        future = self.producer.send(topic, message)
        try:
            record_metadata = future.get(timeout=10)
            return record_metadata
        except Exception as e:
            raise Exception(f"Failed to send message to Kafka: {str(e)}") 