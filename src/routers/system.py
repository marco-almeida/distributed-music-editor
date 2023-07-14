from fastapi import APIRouter

router = APIRouter(tags=["system"])
from routers.music import job_info


@router.get("/job")
async def list_all_jobs():
    return [x for x in job_info]


@router.get("/job/{job_id}")
async def list_job(job_id: str):
    return job_info[job_id]


@router.post("/reset")
async def reset():
    pass
