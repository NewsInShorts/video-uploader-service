from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.services.auth_manager import AuthManager
from apscheduler.schedulers.background import BackgroundScheduler
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


auth_manager = AuthManager.get_instance()

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})

@app.get("/")
async def health_check_2():
    return JSONResponse(content={"status": "ok"})

@app.on_event("startup")
def start_scheduler():
    auth_manager = AuthManager.get_instance()
    scheduler = BackgroundScheduler()
    scheduler.add_job(auth_manager.load_all_from_db, 'interval', minutes=3, id='load_db_job')
    scheduler.start()
    logging.info("Scheduler started on FastAPI startup")
    import atexit
    atexit.register(lambda: scheduler.shutdown())
