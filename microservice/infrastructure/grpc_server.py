from concurrent import futures
import grpc
from microservice.core.config import settings
from microservice.core.logging import logger

class BaseGRPCServer:
    def __init__(self, service, servicer):
        self.service = service
        self.servicer = servicer
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
    def add_services(self):
        # Регистрация сервисов
        pass
    
    def start(self):
        self.add_services()
        self.server.add_insecure_port(settings.GRPC_SERVER)
        self.server.start()
        logger.info(f"gRPC Server started on {settings.GRPC_SERVER}")
        
        try:
            while True:
                # Бесконечный цикл работы сервера
                pass
        except KeyboardInterrupt:
            self.server.stop(0)
            logger.info("gRPC Server stopped") 