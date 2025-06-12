from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)

RESPONSE_TIME = Histogram(
    'http_response_time_seconds',
    'HTTP Response Time',
    ['method', 'endpoint']
)

def setup_instrumentator(app):
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/metrics", "/health"],
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        env_var_name="ENABLE_METRICS",
    )
    
    instrumentator.instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=False,
        tags=["monitoring"]
    )
    
    # Кастомные метрики
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        method = request.method
        endpoint = request.url.path
        
        with RESPONSE_TIME.labels(method, endpoint).time():
            response = await call_next(request)
            REQUEST_COUNT.labels(method, endpoint, response.status_code).inc()
        
        return response 