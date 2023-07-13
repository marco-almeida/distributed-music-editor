import os

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

router = APIRouter()


@router.get("/file/{file_id}")
async def download_music(file_id: int):
    filename = f"{file_id}.wav"
    dir_path = f"/tmp/distributed-music-editor/processed/{filename}"

    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=dir_path, filename=filename, media_type="application/octet-stream")
