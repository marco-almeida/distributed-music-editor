import ctypes
import os
import time
from typing import List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response
from celery.result import AsyncResult

from celery_tasks.tasks import dispatch_process_music

from .utils import get_music_id, get_track_id

router = APIRouter(prefix="/music", tags=["music"])
music = {}  # music_id to metadata (tracks id...)
jobs = {}  # music_id to celery task id
ROOT = "/tmp/distributed-music-editor"
BYTES_PER_SEC = 5300


@router.post("/")
async def submit_music(request: Request):
    header = request.headers
    if header.get("content-type") != "application/octet-stream":
        raise HTTPException(status_code=415, detail="Invalid media type. Only application/octet-stream accepted.")

    body = await request.body()
    music_id = get_music_id()

    # create folder to store music
    dir_path = ROOT + "/originals"
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
        "size": len(body),
    }

    return {"music_id": music_id, "tracks": music[music_id]["tracks"]}


@router.get("/")
async def list_all_music() -> List[dict]:
    return [{"music_id": x["music_id"], "tracks": x["tracks"]} for x in music.values()]


@router.post("/{music_id}")
async def process_music(music_id: int, tracks: List[int]):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")
    tracks = set(tracks)
    if any(track_id not in [x["track_id"] for x in music[music_id]["tracks"]] for track_id in tracks):
        raise HTTPException(status_code=405, detail="Track not found")

    # track id to name
    tracks_str = [x["name"] for x in music[music_id]["tracks"] if x["track_id"] in tracks]

    # dispatch processing which will divide music into chunks and process each chunk in parallel
    task = dispatch_process_music.delay(music_id, tracks_str, 3 * 1000)
    print(task)
    print(type(task))
    ts = time.time()
    music[music_id]["start_time"] = ts
    jobs[music_id] = {"job_id": task.id, "size": music[music_id]["size"], "music_id": music_id, "tracks": tracks, "time": int(ts)}
    return Response(status_code=200)


@router.get("/{music_id}")
async def get_music_progress(music_id: int):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")

    if music_id not in jobs:
        return {"progress": 0}

    file_hash_func = lambda x: ctypes.c_size_t(hash(f"{music_id}|{x}")).value

    job = jobs[music_id]
    job_id = job["job_id"]
    print(job)
    print(type(job))
    print(job_id)
    print(type(job_id))
    job_obj = AsyncResult(job_id)
    print(type(job_obj))
    print(job_obj.result)
    print(job_obj.state)
    ts = time.time() - music[music_id]["start_time"]
    # task_info = get_task_info(job["job_id"])
    # total_time = task_info["task_result"] if task_info["task_status"] == "SUCCESS" else -1
    total_time = -1
    elapsed_time = total_time if total_time != -1 else ts

    jobs[music_id]["time"] = int(elapsed_time * 1000)  # to ms

    # determine progress
    progress = int(elapsed_time * BYTES_PER_SEC / jobs[music_id]["size"] * 100)
    if progress >= 100:
        progress = 99
    progress = 100 if total_time != -1 else progress

    return {"progress": progress}


# TODO, ta music/file/id, trocar dps
# @router.get("/file/{file_id}")
# async def download_music(file_id: int):
#     return FileResponse(path=f"/tmp/distributed-music-editor/processed/{file_id}", filename=f"/{file_id}", media_type="text/wav")
