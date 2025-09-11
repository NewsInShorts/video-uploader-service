import os
import logging
import socket

def get_pod_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

class BaseConfig:
    
    LOG_LEVEL = logging.INFO
    
    CLIENT_SECRETS_FILE = "/Users/madhursharma/Downloads/client_secret_102980865404-82jd7n2hlc65553v0pbhc543tns90dg0.apps.googleusercontent.com.json"
    
    THUMBNAIL_IMAGE_SIZE = 10 # MB
    VIDEO_FILE_SIZE = 500 #MB
    
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DB = "video-uploader"
    MONGO_COLLECTION = "UploadRequests"
    
    # REDIRECT_URI = "http://localhost:8080/auth/oauth2callback?channel_id="
    REDIRECT_URI = "http://localhost:8080/auth/channel"
    
class ProductionConfig(BaseConfig):
    
    LOG_LEVEL = logging.INFO
    
    CLIENT_SECRETS_FILE  = "/var/secrets/google/yt_secret.json"
    
    MONGO_URI = "mongodb://root:superman@172.15.0.48,172.15.0.2,172.15.0.177/admin?replicaSet=ind-uploader-mongo-rs"
    MONGO_DB = "video-uploader"
    MONGO_COLLECTION = "UploadRequests"
    # REDIRECT_URI = "http://" + get_pod_ip() + ":8080/auth/channel"
    REDIRECT_URI = "http://localhost:8080/auth/channel"
    
env = os.getenv("APP_ENV", "development").lower()

if env == "production":
    Config = ProductionConfig()

else:
    Config = BaseConfig()