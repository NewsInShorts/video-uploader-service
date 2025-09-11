import logging
import os
from app.config import Config
from app.services.auth_manager import AuthManager
from fastapi import APIRouter, HTTPException, Request
import google_auth_oauthlib.flow
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter()

auth_manager = AuthManager.get_instance()


@router.post("/{channel_id}")
def authenticate_channel(channel_id: str):
    if not channel_id.strip():
        raise HTTPException(status_code=400, detail="Channel name cannot be empty")

    try:
        logger.info(f"Authenticating channel: {channel_id}")
        return auth_manager.authenticate_channel(channel_id)
    except Exception as e:
        logger.exception(f"Failed to authenticate channel {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")



@router.get("/cache")
def get_cache():
    try:
        return {"cache": auth_manager.list_cached_channels()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cache: {str(e)}")
        
        

@router.get("/load-cache")
def load_cache():
    try:
        return {"cache": auth_manager.load_all_from_db()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load cache: {str(e)}")
        
        

CLIENT_SECRETS_FILE = Config.CLIENT_SECRETS_FILE
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = Config.REDIRECT_URI


@router.get("/channel")
async def authorize(request: Request):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )
    channel_id = request.query_params.get("id")
    
    if not channel_id:
         return JSONResponse(
                    status_code=400,
                    content={"error": "Missing required parameter: channel_id"}
                )
     
    
    flow.redirect_uri = REDIRECT_URI + channel_id

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )

    request.session["state"] = state

    return RedirectResponse(authorization_url)


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

@router.get("/oauth2callback")
async def oauth2callback(request: Request):
    try:
        state = request.session.get("state")
        if not state:
            raise HTTPException(status_code=400, detail="Missing OAuth state in session")

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
        )
        
        channel_id = request.query_params.get("channel_id")
        if not channel_id:
             return JSONResponse(
                        status_code=400,
                        content={"error": "Missing required parameter: channel_id"}
                    )
         
        flow.redirect_uri = REDIRECT_URI + channel_id

        authorization_response = str(request.url)
        flow.fetch_token(authorization_response=authorization_response)

        creds = flow.credentials
        if not creds:
            raise HTTPException(status_code=400, detail="Failed to retrieve credentials")
        
        auth_manager._save_token(channel_id, creds)

        request.session["credentials"] = creds.to_json()
        
        return JSONResponse(content={"message": "Authentication Successful!"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")       