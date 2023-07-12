import logging
import os
import sys

# from config.celery_utils import create_celery
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import music

# needed to make absolute imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)03d: %(module)17s->%(funcName)-15s - [%(levelname)7s] - %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)

logger = logging.getLogger().getChild("System")

app = FastAPI(title="Distributed Music Editor - Advanced Sound Systems", description="A distributed music editor", version="0.1.0")
# app.celery_app = create_celery()
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(music.router)
# celery = app.celery_app

logger.info(f"Available endpoints: {[x.path for x in app.routes]}")
