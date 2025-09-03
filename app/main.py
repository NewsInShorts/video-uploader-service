from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.middleware.logging_middleware import setup_logging, RequestIDMiddleware
from app.routes.video_routes import router as video_router
from app.routes.auth_routes import router as auth_routes
import logging
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(title="Video Uploader Service")

app.add_middleware(SessionMiddleware, secret_key="d5a0e44a8579f59cf624f3e2989d8a43c2ff62f53c98c55c8db39a3dd8b07917")

setup_logging(app)
app.add_middleware(RequestIDMiddleware)

app.include_router(video_router, prefix="/api", tags=["Video Upload"])
app.include_router(auth_routes, prefix="/auth", tags=["Channel Auth"])

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})

