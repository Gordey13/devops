from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.infrastructure.database.postgres import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    # Проверка подключения к БД
    try:
        await db.execute(text("SELECT 1"))
        db_status = "OK"
    except Exception as e:
        db_status = f"Error: {str(e)}"
    
    # Проверка подключения к Kafka
    kafka_status = "OK"
    # Здесь можно добавить реальную проверку Kafka
    
    return {
        "status": "UP",
        "services": {
            "database": db_status,
            "kafka": kafka_status
        }
    } 