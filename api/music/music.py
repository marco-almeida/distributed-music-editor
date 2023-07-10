import os
import sys
from typing import List

import pika
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import Response

from .utils import deep_process_music, get_music_id, get_track_id

music = {}
router = APIRouter()
ROOT = "/tmp/distributed-music-editor"


@router.post("/music")
async def submit_music(request: Request):
    header = request.headers
    if header["content-type"] != "application/octet-stream":
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
    }

    return music[music_id]


@router.get("/music")
async def list_all_music() -> List[dict]:
    return [x for x in music.values()]


@router.post("/music/{music_id}")
async def process_music(music_id: int, tracks: List[int], background_tasks: BackgroundTasks):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")
    tracks = set(tracks)
    if any(track_id not in [x["track_id"] for x in music[music_id]["tracks"]] for track_id in tracks):
        raise HTTPException(status_code=405, detail="Track not found")

    # create folder to store processed music
    dir_path = ROOT + f"/processed/{music_id}"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # background_tasks.add_task(deep_process_music, f"{ROOT}/originals/{music_id}.mp3", dir_path)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()

    channel.queue_declare(queue="task_queue", durable=True)

    channel.basic_publish(
        exchange="",
        routing_key="task_queue",
        body=str(music_id),
        properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
    )

    connection.close()
    return Response(status_code=200)


@router.get("/music/{music_id}")
async def get_music_progress(music_id: int):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")

    return {"progress": 21}
