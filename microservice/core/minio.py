from minio import Minio
from microservice.core.config import Settings

class MinioClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None

    async def connect(self):
        self.client = Minio(
            self.settings.MINIO_ENDPOINT,
            access_key=self.settings.MINIO_ACCESS_KEY,
            secret_key=self.settings.MINIO_SECRET_KEY,
            secure=True
        )
        
        # Проверяем существование бакета
        if not self.client.bucket_exists(self.settings.MINIO_BUCKET):
            self.client.make_bucket(self.settings.MINIO_BUCKET)

    async def disconnect(self):
        # Minio client не требует явного закрытия
        pass

    async def upload_file(self, object_name: str, data: str):
        if not self.client:
            raise Exception("Minio client not connected")
        
        try:
            self.client.put_object(
                bucket_name=self.settings.MINIO_BUCKET,
                object_name=object_name,
                data=data.encode('utf-8'),
                length=len(data.encode('utf-8')),
                content_type='text/plain'
            )
        except Exception as e:
            raise Exception(f"Failed to upload file to Minio: {str(e)}")

    async def download_file(self, object_name: str) -> str:
        if not self.client:
            raise Exception("Minio client not connected")
        
        try:
            response = self.client.get_object(
                bucket_name=self.settings.MINIO_BUCKET,
                object_name=object_name
            )
            return response.read().decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to download file from Minio: {str(e)}") 