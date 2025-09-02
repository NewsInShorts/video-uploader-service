from fastapi import APIRouter, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.services.youtube_service import YouTubeUploader
from app.utils.file_validator import validate_file
from app.config import Config
import time, shutil, os, logging
from bson import ObjectId
from app.services.mongo_service import MongoService
from app.models.upload_request import UploadRequest

logger = logging.getLogger(__name__)
router = APIRouter()
mongo_service = MongoService()

client_secrets_file = Config.CLIENT_SECRETS_FILE
uploader = YouTubeUploader(client_secrets_file)

@router.post("/upload-video")
async def upload_video(
    channel_id: str = Form(...),
    title: str = Form(..., max_length=100),
    description: str = Form(..., max_length=5000),
    video_file: UploadFile = Form(...),
    thumbnail_file: UploadFile = Form(...),
    category_id: int = Form(22)
):
    logger.info(f"Upload request received for channel_id={channel_id}, title={title}")

    if not channel_id.strip():
        raise HTTPException(status_code=400, detail="Channel ID cannot be empty")
    if not title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    if not description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    validate_file(video_file, ["mp4", "mov", "avi"], Config.VIDEO_FILE_SIZE)
    validate_file(thumbnail_file, ["jpg", "jpeg", "png"], Config.THUMBNAIL_IMAGE_SIZE)

    timestamp = int(time.time())
    temp_video_path = f"/tmp/{timestamp}_{video_file.filename}"
    temp_thumb_path = f"/tmp/{timestamp}_{thumbnail_file.filename}"
    
    request_doc = UploadRequest(
    channel_id=channel_id,
    title=title,
    description=description,
    video_filename=video_file.filename,
    thumbnail_filename=thumbnail_file.filename,
    category_id=category_id
    )
    request_id = mongo_service.insert_request(request_doc)
    

    try:
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)

        with open(temp_thumb_path, "wb") as buffer:
            shutil.copyfileobj(thumbnail_file.file, buffer)

        video_url = uploader.upload_video(
            channel_id=channel_id,
            title=title,
            description=description,
            video_path=temp_video_path,
            thumbnail_path=temp_thumb_path,
            category_id=category_id
        )
        
        mongo_service.update_request_status(ObjectId(request_id), "SUCCESS", video_url=video_url)

        return JSONResponse(content={"video_url": video_url})

    except Exception as e:
        logger.exception(f"Unexpected error during video upload: {str(e)}")
        if request_id:
            mongo_service.update_request_status(ObjectId(request_id), "FAILED", error_message=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for file_path in [temp_video_path, temp_thumb_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to delete {file_path}: {cleanup_error}")
