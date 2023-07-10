import os
from typing import List

import pika
from celery import group
from celery_tasks.tasks import deep_process_music
from config.celery_utils import get_task_info
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from starlette.responses import JSONResponse

router = APIRouter(prefix="/music", tags=["music"])
music_counter = 0
track_counter = 0


def get_music_id():
    global music_counter
    ctr = music_counter
    music_counter = music_counter + 1
    return ctr


def get_track_id():
    global track_counter
    ctr = track_counter
    track_counter = track_counter + 1
    return ctr


music = {}
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
    }

    return music[music_id]


@router.get("/")
async def list_all_music() -> List[dict]:
    return [x for x in music.values()]


@router.post("/{music_id}")
async def process_music(music_id: int, tracks: List[int]):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")
    tracks = set(tracks)
    if any(track_id not in [x["track_id"] for x in music[music_id]["tracks"]] for track_id in tracks):
        raise HTTPException(status_code=405, detail="Track not found")

    # create folder to store processed music
    dir_path = ROOT + f"/processed/{music_id}"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    input_file = f"{ROOT}/originals/{music_id}.mp3"
    task = deep_process_music.apply_async(
        args=(
            input_file,
            dir_path,
        )
    )

    print("dewin it", hash(task.id), task.status)
    return Response(status_code=200)


@router.get("/{music_id}")
async def get_music_progress(music_id: int):
    if music_id not in music:
        raise HTTPException(status_code=404, detail="Music not found")

    return {"progress": 21}


@router.get("/task/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """
    Return the status of the submitted Task
    """
    return get_task_info(task_id)


# @router.post("/parallel")
# async def get_universities_parallel(country: Country) -> dict:
#     """
#     Return the List of universities for the countries for e.g ["turkey","india","australia"] provided
#     in input in a sync way. This will use Celery to perform the subtasks in a parallel manner
#     """

#     data: dict = {}
#     tasks = []
#     for cnt in country.countries:
#         tasks.append(get_university_task.s(cnt))
#     # create a group with all the tasks
#     job = group(tasks)
#     result = job.apply_async()
#     ret_values = result.get(disable_sync_subtasks=False)
#     for result in ret_values:
#         data.update(result)
#     return data
