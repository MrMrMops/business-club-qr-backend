from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.qr import router as qr_router


app = FastAPI(
    title="Business Club QR Backend",
    version="1.0.0",
)


app.include_router(health_router)
app.include_router(qr_router)