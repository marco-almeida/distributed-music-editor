import hashlib
import os
import time
from typing import List

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from celery_tasks.tasks import dispatch_process_music

from .utils import get_music_id, get_track_id

router = APIRouter(prefix="/music", tags=["music"])
music = {}  # music_id to metadata (tracks id...)
jobs = {}  # music_id to celery task id
ROOT = "/tmp/distributed-music-editor"


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

    ts = time.time()
    music[music_id]["start_time"] = ts
    jobs[music_id] = {"job_id": task.id, "size": music[music_id]["size"], "music_id": music_id, "tracks": tracks, "time": int(ts)}
    return Response(status_code=200)


from celery.result import GroupResult


@router.get("/{music_id}")
async def get_music_progress(music_id: int):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")

    if music_id not in jobs:
        return {"progress": 0}

    job = jobs[music_id]
    job_id = job["job_id"]
    job_obj = AsyncResult(job_id)
    children: GroupResult = job_obj.children
    try:
        children_tasks = [y for x in children for y in x]
    except:
        return {"progress": 0}
    # progress is the number of processed tasks / total tasks
    progress = len([task for task in children_tasks if task.status == "SUCCESS"]) / len(children_tasks) * 100
    msg = {"progress": int(progress)}
    if progress == 100:
        msg["instruments"] = []
        for track in music[music_id]["tracks"]:
            channel_name = track["name"]
            name_to_be_hashed = f"{music_id}|{channel_name}".encode()
            file_name = int(hashlib.md5(name_to_be_hashed).hexdigest(), 16)
            msg["instruments"].append({"name": channel_name, "track": f"http://localhost:8000/file/{file_name}"})
        name_to_be_hashed = f"{music_id}|final".encode()
        file_name = int(hashlib.md5(name_to_be_hashed).hexdigest(), 16)
        msg["final"] = f"http://localhost:8000/file/{file_name}"
        print(f"Final track: {file_name}. obtained from {name_to_be_hashed}")
    return msg
