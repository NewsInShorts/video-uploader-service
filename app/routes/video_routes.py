import os
import time
import uuid
import shutil
import logging
from bson import ObjectId
from fastapi import APIRouter, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from googleapiclient.errors import HttpError

from app.services.youtube_service import YouTubeUploaderService
from app.services.mongo_service import MongoService
from app.utils.file_validator import validate_file
from app.models.upload_request import UploadRequest
from app.services.auth_manager import AuthManager
from app.config import Config

logger = logging.getLogger(__name__)
router = APIRouter()
mongo_service = MongoService()

auth_manager = AuthManager.get_instance()
uploader = YouTubeUploaderService(auth_manager)


@router.post("/upload-video")
async def upload_video(
    channel_id: str = Form(...),
    title: str = Form(..., max_length=100),
    description: str = Form(..., max_length=5000),
    video_file: UploadFile = Form(...),
    thumbnail_file: UploadFile = Form(...),
    category_id: int = Form(22)
):
    start_time = time.time()
    logger.info(f"Upload request received for channel_id={channel_id}, title={title}")

    if not channel_id.strip():
        raise HTTPException(status_code=400, detail="Channel ID cannot be empty")
    if not title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    if not description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    if category_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid category_id")

    validate_file(video_file, ["mp4", "mov", "avi"], Config.VIDEO_FILE_SIZE)
    validate_file(thumbnail_file, ["jpg", "jpeg", "png"], Config.THUMBNAIL_IMAGE_SIZE)

    request_id = None
    unique_id = uuid.uuid4().hex
    temp_video_path = f"/tmp/{unique_id}_{os.path.basename(video_file.filename)}"
    temp_thumb_path = f"/tmp/{unique_id}_{os.path.basename(thumbnail_file.filename)}"

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

        # -------- Upload to YouTube --------
        logger.info(f"Uploading video for request_id={request_id}")
        video_url = uploader.upload_video(
            channel_id=channel_id, 
            title=title,
            description=description,
            video_path=temp_video_path,
            thumbnail_path=temp_thumb_path,
            category_id=category_id
        )

        elapsed = round(time.time() - start_time, 2)
        mongo_service.update_request_status(ObjectId(request_id), "SUCCESS", video_url=video_url)
        logger.info(f"Video uploaded successfully in {elapsed}s",
                    extra={"request_id": str(request_id), "video_url": video_url})

        return JSONResponse(content={"video_url": video_url, "elapsed_time": elapsed})

    except HttpError as he:
        error_msg = f"YouTube API error: {he}"
        logger.error(error_msg, extra={"request_id": str(request_id)})
        mongo_service.update_request_status(ObjectId(request_id), "FAILED", error_message=error_msg)
        raise HTTPException(status_code=502, detail="YouTube API error")

    except Exception as e:
        error_msg = f"Unexpected error during video upload: {str(e)}"
        logger.exception(error_msg, extra={"request_id": str(request_id)})
        mongo_service.update_request_status(ObjectId(request_id), "FAILED", error_message=error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        for file_path in [temp_video_path, temp_thumb_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to delete {file_path}: {cleanup_error}",
                                   extra={"request_id": str(request_id)})
