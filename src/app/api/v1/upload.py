from fastapi import APIRouter, UploadFile, File, Depends
from ...core.utils.s3 import upload_file_to_s3, generate_s3_url
from ...core.exceptions.http_exceptions import CustomException
from ...api.dependencies import get_current_user
from ...schemas.user import User 

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    key: str | None = None
    try:
        key = upload_file_to_s3(file, current_user["id"])
    except Exception as e:
        raise CustomException(500, f"Failed to upload file: {key}. Error: {str(e)}")

    try:
        url = generate_s3_url(key)
    except Exception as e:
        raise CustomException(500, f"Could not generate URL for file key: {key}")

    return {"key": key, "url": url}


@router.get("/upload/{key}")
async def get_file(key: str):
    try:
        url = generate_s3_url(key)
    except Exception as e:
        raise CustomException(500, f"Could not generate URL for file key: {key}")
    
    return {"url": url}