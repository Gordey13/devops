from fastapi import FastAPI
from microservice.core.monitoring import instrumentator
from microservice.core.logging import setup_logging

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