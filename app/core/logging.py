import logging
import sys
import json
from pythonjsonlogger import jsonlogger
from app.core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['service'] = "my_microservice"
        log_record['environment'] = settings.ENVIRONMENT

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    
    # JSON-форматер для production
    json_handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter('%(asctime)s %(level)s %(name)s %(message)s')
    json_handler.setFormatter(formatter)
    
    # Консольный форматтер для разработки
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(console_handler)
    else:
        logger.addHandler(json_handler)
    
    # Настройка логов для библиотек
    for logger_name in ['uvicorn', 'aiokafka', 'sqlalchemy']:
        logging.getLogger(logger_name).handlers = []
        logging.getLogger(logger_name).propagate = True

    return logger 