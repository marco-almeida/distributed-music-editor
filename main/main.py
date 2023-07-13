import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import music
from routers.utils import delete_folder


@asynccontextmanager
async def lifespan(app: FastAPI):
    # before start up
    delete_folder("/tmp/distributed-music-editor")
    os.makedirs("/tmp/distributed-music-editor", exist_ok=True)
    yield
    delete_folder("/tmp/distributed-music-editor")


logging.basicConfig(
    format="%(asctime)s,%(msecs)03d: %(module)17s->%(funcName)-15s - [%(levelname)7s] - %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)

logger = logging.getLogger().getChild("System")

app = FastAPI(
    title="Distributed Music Editor - Advanced Sound Systems", description="A distributed music editor", version="1.0.0", lifespan=lifespan
)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(music.router)

logger.info(f"Available endpoints: {[x.path for x in app.routes]}")
