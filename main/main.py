import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from routers import music, system
from routers.utils import delete_folder


@asynccontextmanager
async def lifespan(app: FastAPI):
    # before start up
    delete_folder("/tmp/distributed-music-editor")
    os.makedirs("/tmp/distributed-music-editor", exist_ok=True)
    # if processed folder doesnt exist, create it
    delete_folder("/tmp/distributed-music-editor/processed")
    os.makedirs("/tmp/distributed-music-editor/processed", exist_ok=True)
    # if originals folder doesnt exist, create it
    delete_folder("/tmp/distributed-music-editor/originals")
    os.makedirs("/tmp/distributed-music-editor/originals", exist_ok=True)
    yield
    delete_folder("/tmp/distributed-music-editor")
    delete_folder("/tmp/distributed-music-editor/processed")
    delete_folder("/tmp/distributed-music-editor/originals")


logging.basicConfig(
    format="%(asctime)s,%(msecs)03d: %(module)17s->%(funcName)-15s - [%(levelname)7s] - %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)

logger = logging.getLogger().getChild("System")

app = FastAPI(
    title="Distributed Music Editor - Advanced Sound Systems",
    description="A firma Advanced Sound Systems (ASS) encontra-se a desenvolver uma aplicação de karaoke para músicos. Esta aplicação distingue-se por não só remover a voz das músicas, mas também remover instrumentos individuais, permitindo a um músico substituir a performance do músico original pela sua. Este novo serviço será disponibilizado online através de um portal web em que o músico pode fazer upload de um ficheiro de música, analisar os instrumentos que compõem a música, selecionar vários instrumentos e finalmente receber um ficheiro novo em que a música contém apenas esses instrumentos.",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(system.router)


@app.get("/file/{file_id}")
async def download_music(file_id: int):
    filename = f"{file_id}.wav"
    dir_path = f"/tmp/distributed-music-editor/processed/{filename}"

    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=dir_path, filename=filename, media_type="application/octet-stream")


logger.info(f"Available endpoints: {[x.path for x in app.routes]}")
