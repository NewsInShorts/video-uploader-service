import os
import logging

class BaseConfig:
    
    LOG_LEVEL = logging.INFO
    
    CLIENT_SECRETS_FILE = "/Users/madhursharma/Downloads/client_secret_102980865404-82jd7n2hlc65553v0pbhc543tns90dg0.apps.googleusercontent.com.json"
    
    THUMBNAIL_IMAGE_SIZE = 10 # MB
    VIDEO_FILE_SIZE = 500 #MB
    
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DB = "video_uploader"
    MONGO_COLLECTION = "upload_requests"
    
    REDIRECT_URI = "http://localhost:8000/auth/oauth2callback?channel_id="
    
class ProductionConfig(BaseConfig):
    
    LOG_LEVEL = logging.INFO
    
    CLIENT_SECRETS_FILE  = "/var/secrets/google/yt-creds.json"
    
    MONGO_URI = "mongodb://root:superman@172.15.0.48,172.15.0.2,172.15.0.177/admin?replicaSet=ind-uploader-mongo-rs"
    MONGO_DB = "video_uploader"
    MONGO_COLLECTION = "UploadRequests"
    
    REDIRECT_URI = "http://localhost:8000/auth/oauth2callback?channel_id="
    
env = os.getenv("APP_ENV", "development").lower()

if env == "production":
    Config = ProductionConfig()

else:
    Config = BaseConfig()