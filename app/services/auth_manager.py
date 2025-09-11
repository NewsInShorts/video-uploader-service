import os
import json
import logging
from app.config import Config
import google_auth_oauthlib.flow
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from pymongo import MongoClient, errors
from datetime import datetime

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
logger = logging.getLogger("auth_manager")


class AuthManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AuthManager(
                client_secrets_file=Config.CLIENT_SECRETS_FILE,
                mongo_uri=Config.MONGO_URI,
                db_name=Config.MONGO_DB
            )
        return cls._instance
    
    def __init__(self, client_secrets_file: str, mongo_uri: str, db_name: str):
        if not client_secrets_file or not os.path.exists(client_secrets_file):
            logger.error(f"Client secrets file not found: {client_secrets_file}")
            raise FileNotFoundError(f"Client secrets file not found: {client_secrets_file}")

        if not mongo_uri or not mongo_uri.strip():
            logger.error("Mongo URI cannot be empty")
            raise ValueError("Mongo URI cannot be empty")

        try:
            self.client_secrets_file = client_secrets_file
            self.client_id, self.client_secret, self.token_uri = self._load_client_secrets(client_secrets_file)
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
        except errors.ConnectionFailure as e:
            logger.exception("Failed to connect to MongoDB")
            raise RuntimeError(f"MongoDB connection failed: {str(e)}") from e

        self.db = self.client[db_name]
        self.tokens = self.db["ChannelTokens"]

        self._cache = {}
        logger.info("AuthManager initialized successfully")
    
    
    def _load_client_secrets(self, client_secrets_file: str):
        with open(client_secrets_file, "r") as f:
            data = json.load(f)
            info = data.get("installed") or data.get("web")
            return info["client_id"], info["client_secret"], info["token_uri"]


    def _save_token(self, channel_id: str, creds: Credentials):
        if not channel_id or not channel_id.strip():
            raise ValueError("Channel name cannot be empty")
        if not creds:
            raise ValueError("Credentials object is required")

        try:
            data = {
                "channel_id": channel_id,
                "token": creds.to_json(),
                "updated_at": datetime.utcnow(),
            }
            self.tokens.update_one({"channel_id": channel_id}, {"$set": data}, upsert=True)
            self._cache[channel_id] = creds
            logger.info(f"Token saved for channel '{channel_id}'")
        except Exception as e:
            logger.exception("Failed to save token to MongoDB")
            raise RuntimeError(f"Error saving token for channel '{channel_id}': {str(e)}") from e

    def load_all_from_db(self):
        try:
            records = self.tokens.find({})
            loaded_channels = []
    
            for record in records:
                channel_id = record.get("channel_id")
                if not channel_id:
                    continue
    
                try:
                    token_data = json.loads(record["token"])
    
                    creds = Credentials(
                        token=token_data.get("access_token"),
                        refresh_token=token_data.get("refresh_token"),
                        token_uri=self.token_uri,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        scopes=SCOPES,
                    )
    
                    self._cache[channel_id] = creds
                    loaded_channels.append(channel_id)
                    logger.info(f"Token loaded from DB for channel '{channel_id}'")
    
                except Exception as inner_e:
                    logger.error(f"Failed to load token for channel '{channel_id}': {str(inner_e)}")
    
            return loaded_channels
    
        except Exception as e:
            logger.exception("Error loading tokens from MongoDB")
            raise RuntimeError(f"Error loading tokens for all channels: {str(e)}") from e


    def _load_from_db(self, channel_id: str):
        try:
            record = self.tokens.find_one({"channel_id": channel_id})
            if record and "token" in record:
                
                
                token_data = json.loads(record["token"])
                
                creds = Credentials(
                    token=token_data.get("access_token"),
                    refresh_token=token_data.get("refresh_token"),
                    token_uri=self.token_uri,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=SCOPES,
                )
                # creds = Credentials.from_authorized_user_info(
                #     json.loads(record["token"]), SCOPES
                # )
                self._cache[channel_id] = creds
                logger.info(f"----- {self._cache}")
                logger.info(f"Token loaded from DB for channel '{channel_id}'")
                return creds
            logger.warning(f"No token found in DB for channel '{channel_id}'")
            return None
        except Exception as e:
            logger.exception("Error loading token from MongoDB")
            raise RuntimeError(f"Error loading token for channel '{channel_id}': {str(e)}") from e

    def get_credentials(self, channel_id: str) -> Credentials:
        if not channel_id or not channel_id.strip():
            raise ValueError("Channel name cannot be empty")

        creds = self._cache.get(channel_id)
        if creds:
            logger.info(f"Credentials for channel '{channel_id}' loaded from cache")
        else:
            creds = self._load_from_db(channel_id)
            if creds:
                logger.info(f"Credentials for channel '{channel_id}' loaded from MongoDB")
            else:
                # Neither in cache nor DB
                logger.warning(f"Credentials NOT FOUND for channel '{channel_id}'")
                return None

        try:
            if creds.expired and creds.refresh_token:
                logger.info(f"Refreshing credentials for channel '{channel_id}'")
                creds.refresh(google.auth.transport.requests.Request())
                self._save_token(channel_id, creds)
        except Exception as e:
            logger.exception(f"Failed to refresh credentials for '{channel_id}'")
            raise RuntimeError(f"Failed to refresh credentials: {str(e)}") from e

        return creds

    def authenticate_channel(self, channel_id: str):
        if not channel_id or not channel_id.strip():
            raise ValueError("Channel name cannot be empty")

        try:
            logger.info(f"Starting authentication flow for channel '{channel_id}'")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, SCOPES
            )
            #creds = flow.run_console()  # or flow.run_local_server(port=0)
            creds = flow.run_local_server(port=0)
            self._save_token(channel_id, creds)
            logger.info(f"Channel '{channel_id}' authenticated successfully")
            return {"message": f"Channel '{channel_id}' authenticated successfully"}
        except FileNotFoundError:
            logger.error("Client secrets file not found during authentication")
            raise
        except Exception as e:
            logger.exception("Error during channel authentication")
            raise RuntimeError(f"Authentication failed for channel '{channel_id}': {str(e)}") from e
            
    def list_cached_channels(self):
        result = {}
        for channel_id, creds in self._cache.items():
            result[channel_id] = {
                "valid": creds.valid,
                "expired": creds.expired,
                "scopes": creds.scopes,
            }
            return result
