from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.middleware.logging_middleware import setup_logging, RequestIDMiddleware
from app.routes.video_routes import router as video_router
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Video Uploader Service")

setup_logging(app)
app.add_middleware(RequestIDMiddleware)

app.include_router(video_router, prefix="/api", tags=["Video Upload"])

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})