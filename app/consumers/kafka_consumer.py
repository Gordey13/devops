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
    )
    
    await consumer.start()
    try:
        async for msg in consumer:
            logger.info(f"Received message: {msg.value}")
            # Process message here
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume()) 