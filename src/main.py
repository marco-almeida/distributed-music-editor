import argparse
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from routers import music, system
from routers.utils import delete_folder, make_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # before start up
    delete_folder("/tmp/distributed-music-editor")
    make_dirs("/tmp/distributed-music-editor/processed", "/tmp/distributed-music-editor/originals")
    yield
    # after shutdown
    delete_folder("/tmp/distributed-music-editor")


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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="API for the Distributed Music Editor", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-i", "--ip", type=str, help="API IP", default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, help="API Port", default=7123)
    args = parser.parse_args()
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import settings

    settings.ip = args.ip
    settings.port = args.port

    uvicorn.run("main:app", host=args.ip, port=args.port)
