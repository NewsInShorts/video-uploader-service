import os
import logging
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.services.auth_manager import AuthManager

logger = logging.getLogger("youtube_uploader")


class YouTubeUploaderService:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager

    def upload_video(
        self,
        channel_id: str,
        title: str,
        description: str,
        video_path: str,
        thumbnail_path: str = None,
        category_id: int = 22,
        privacy_status: str = "public"
    ):
        logger.info("Preparing to upload video",
                    extra={"channel_id": channel_id, "title": title})

        if not channel_id or not channel_id.strip():
            raise ValueError("Channel name cannot be empty")
        if not title or len(title) > 100:
            raise ValueError("Title is required and must be <= 100 characters")
        if not description or len(description) > 5000:
            raise ValueError("Description is required and must be <= 5000 characters")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if thumbnail_path and not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f"Thumbnail file not found: {thumbnail_path}")
        if privacy_status not in ["public", "private", "unlisted"]:
            raise ValueError("privacy_status must be 'public', 'private', or 'unlisted'")

        creds = self.auth_manager.get_credentials(channel_id)
        if not creds:
            logger.error(f"Channel '{channel_id}' not authenticated")
            raise RuntimeError(f"Channel '{channel_id}' not authenticated. Call /auth first.")

        youtube = build("youtube", "v3", credentials=creds)

        try:
            logger.info("Starting video upload...",
                        extra={"channel_id": channel_id, "video_file": video_path})
            request = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "channelId": channel_id,
                        "categoryId": str(category_id),
                        "title": title,
                        "description": description,
                    },
                    "status": {"privacyStatus": privacy_status},
                },
                media_body=MediaFileUpload(video_path, resumable=True),
            )
            response = request.execute()
            video_id = response.get("id")
            if not video_id:
                logger.error("YouTube API did not return a video ID")
                raise RuntimeError("Failed to upload video, no video ID returned")

            logger.info("Video uploaded successfully",
                        extra={"channel_id": channel_id, "video_id": video_id})

            if thumbnail_path:
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path),
                    ).execute()
                    logger.info("Thumbnail uploaded",
                                extra={"video_id": video_id, "thumbnail": thumbnail_path})
                except HttpError as he:
                    logger.warning(f"Thumbnail upload failed: {he}",
                                   extra={"video_id": video_id})

            return f"https://youtu.be/{video_id}"

        except HttpError as he:
            logger.error(f"YouTube API error: {he}", exc_info=True,
                         extra={"channel_id": channel_id})
            raise RuntimeError(f"YouTube API error: {he}") from he
        except Exception as e:
            logger.exception("Unexpected error during upload",
                             extra={"channel_id": channel_id})
            raise RuntimeError(f"Unexpected error: {str(e)}") from e
