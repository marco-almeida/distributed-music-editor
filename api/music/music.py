import os
from typing import List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from .utils import get_music_id, get_track_id
import asyncio

music = {}
router = APIRouter()


@router.post("/music")
async def submit_music(request: Request):
    header = request.headers
    if header["content-type"] != "application/octet-stream":
        raise HTTPException(status_code=415, detail="Invalid media type. Only application/octet-stream accepted.")

    body = await request.body()
    music_id = get_music_id()

    # create folder to store music
    working_dir = os.getcwd()
    dir_path = working_dir + "/stored_music"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # write to file
    with open(f"{dir_path}/{music_id}.mp3", "wb") as f:
        f.write(body)

    # store music id
    music[music_id] = {
        "music_id": music_id,
        "tracks": [
            {"name": "drums", "track_id": get_track_id()},
            {"name": "bass", "track_id": get_track_id()},
            {"name": "vocals", "track_id": get_track_id()},
            {"name": "other", "track_id": get_track_id()},
        ],
    }

    return music[music_id]


@router.get("/music")
async def list_all_music() -> List[dict]:
    return [x for x in music]


@router.post("/music/{music_id}")
async def process_music(music_id: int, tracks: List[int]):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")
    if any(track_id not in [x["track_id"] for x in music[music_id]["tracks"]] for track_id in tracks):
        raise HTTPException(status_code=405, detail="Track not found")
    
    # dispatch
    await asyncio.sleep(5)
    
    
    return Response(status_code=200)
