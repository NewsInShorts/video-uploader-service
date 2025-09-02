import logging

class Config:
    
    LOG_LEVEL = logging.INFO
    
    CLIENT_SECRETS_FILE = "config.json"
    
    THUMBNAIL_IMAGE_SIZE = 10 #MB
    VIDEO_FILE_SIZE = 500 #MB
    
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DB = "video_uploader"
    MONGO_COLLECTION = "upload_requests"
    
