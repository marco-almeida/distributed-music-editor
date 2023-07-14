from fastapi import APIRouter

router = APIRouter(tags=["system"])
from celery_tasks.tasks import app
from routers.music import job_info, jobs, music
from routers.utils import delete_folder, make_dirs


@router.get("/job")
async def list_all_jobs():
    return [x for x in job_info]


@router.get("/job/{job_id}")
async def list_job(job_id: str):
    return job_info[job_id]


@router.post("/reset")
async def reset():
    # terminate all jobs
    app.control.purge()

    # reset data structures
    music.clear()
    jobs.clear()
    job_info.clear()

    # delete and create folders
    delete_folder("/tmp/distributed-music-editor")
    make_dirs("/tmp/distributed-music-editor/processed", "/tmp/distributed-music-editor/originals")
