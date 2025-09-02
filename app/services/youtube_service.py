import os
import logging
import google_auth_oauthlib.flow
import google.auth.transport.requests
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

logger = logging.getLogger("youtube_uploader")


class YouTubeUploader:
    def __init__(self, client_secrets_file: str, token_file: str = "token.json"):
        if not os.path.exists(client_secrets_file):
            logger.error(f"Client secrets file not found: {client_secrets_file}")
            raise FileNotFoundError(f"Client secrets file not found: {client_secrets_file}")

        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.youtube = self.authenticate()

    def authenticate(self):
        creds = None
        #os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES
                )
                creds = flow.run_console()
                #creds = flow.run_local_server(port=0)

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        return googleapiclient.discovery.build("youtube", "v3", credentials=creds)        


    def upload_video(
        self,
        channel_id: str,
        title: str,
        description: str,
        video_path: str,
        thumbnail_path: str,
        category_id: int
    ):
        if not channel_id.strip():
            raise ValueError("Channel ID cannot be empty")
        if not title.strip():
            raise ValueError("Title cannot be empty")
        if not description.strip():
            raise ValueError("Description cannot be empty")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if thumbnail_path and not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f"Thumbnail file not found: {thumbnail_path}")

        logger.info(f"Uploading video '{title}' to channel {channel_id} (category {category_id})...")

        try:
            request = self.youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "categoryId": str(category_id),
                        "channelId": channel_id,
                        "title": title,
                        "description": description,
                    },
                    "status": {"privacyStatus": "public"},
                },
                media_body=MediaFileUpload(video_path)
            )

            response = request.execute()
            video_id = response.get("id")
            if not video_id:
                logger.error("YouTube API response did not include video ID.")
                raise RuntimeError("Failed to upload video")

            logger.info(f"Video uploaded successfully. Video ID: {video_id}")

            if thumbnail_path:
                try:
                    logger.info(f"Setting thumbnail for video {video_id}...")
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logger.info("Thumbnail uploaded successfully.")
                except HttpError as he:
                    logger.warning(f"Failed to upload thumbnail: {he}")
                except Exception as e:
                    logger.warning(f"Unexpected error uploading thumbnail: {e}")

            return f"https://youtu.be/{video_id}"

        except HttpError as he:
            logger.error(f"YouTube API error: {he}")
            raise RuntimeError(f"YouTube API error: {he}")
        except Exception as e:
            logger.exception(f"Unexpected error during upload: {str(e)}")
            raise RuntimeError(f"Unexpected error during upload: {str(e)}")

  
