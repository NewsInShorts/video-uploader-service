from pymongo import MongoClient
from app.config import Config
from app.models.upload_request import UploadRequest
import logging

logger = logging.getLogger(__name__)

class MongoService:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        self.collection = self.db[Config.MONGO_COLLECTION]

    def insert_request(self, request: UploadRequest) -> str:
        try:
            result = self.collection.insert_one(request.dict())
            logger.info(f"Stored request in MongoDB with _id={result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert request: {e}")
            return None

    def update_request_status(self, request_id: str, status: str, video_url: str = None, error_message: str = None):
        try:
            update_data = {"status": status}
            if video_url:
                update_data["video_url"] = video_url
            if error_message:
                update_data["error_message"] = error_message
            self.collection.update_one({"_id": request_id}, {"$set": update_data})
        except Exception as e:
            logger.error(f"Failed to update request {request_id}: {e}")
