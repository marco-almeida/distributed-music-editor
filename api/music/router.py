import logging
import sys

from fastapi import APIRouter

from . import music  # properties

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)03d: %(module)17s->%(funcName)-15s - [%(levelname)7s] - %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)


_SystemLogger = logging.getLogger().getChild("System")
router = APIRouter()

router.include_router(music.router)
