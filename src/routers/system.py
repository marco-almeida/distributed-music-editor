from celery import Celery
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from routers.music import job_info, jobs, music
from routers.utils import delete_folder, make_dirs

router = APIRouter(tags=["system"])

workers = Celery("celery_tasks.tasks", backend="redis://localhost", broker="pyamqp://guest@localhost//")


@router.get("/job")
async def list_all_jobs():
    return [x for x in job_info]


@router.get("/job/{job_id}")
async def list_job(job_id: str):
    if job_id not in job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_info[job_id]


@router.post("/reset")
async def reset():
    # terminate all jobs
    workers.control.purge()

    # reset data structures
    music.clear()
    jobs.clear()
    job_info.clear()

    # delete and create folders
    delete_folder("/tmp/distributed-music-editor")
    make_dirs("/tmp/distributed-music-editor/processed", "/tmp/distributed-music-editor/originals")
    return Response(status_code=200)
