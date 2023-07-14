# coding: utf-8

__author__ = "Mário Antunes"
__version__ = "1.0"
__email__ = "mario.antunes@ua.pt"
__status__ = "Production"
__license__ = "MIT"


import argparse
import json
import logging
import sys
import time
from random import randint, sample

import requests


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def progressbar(i, prefix="", n=100, size=100, out=sys.stdout):  # Python3.6+
    count = n

    def show(j):
        x = int(size * j / count)
        print(f"{prefix}[{u'█'*x}{('.'*(size-x))}] {j}/{count}", end="\r", file=out, flush=True)
        if j >= n:
            print("\n", flush=True, file=out)

    show(i)


# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


def main(args):
    # Load Test Music
    with open("notfunny.mp3", "rb") as f:
        test_music_data = f.read()

    # Load Eval Music
    with open("notfunny.mp3", "rb") as f:
        eval_music_data = f.read()

    # POST /music
    r = requests.post(f"{args.u}/music", data=test_music_data, headers={"Content-Type": "application/octet-stream"}, timeout=args.t)

    if r.ok:
        json_response = r.json()
        logger.info(f"{json_response}")
        # test_music_id = json_response['music_id']
    else:
        logger.error("Error: POST /music")

    r = requests.post(f"{args.u}/music", data=eval_music_data, headers={"Content-Type": "application/octet-stream"}, timeout=args.t)

    if r.ok:
        json_response = r.json()
        logger.info(f"{json_response}")
        eval_music_id = json_response["music_id"]
        tracks = [track["track_id"] for track in json_response["tracks"]]
    else:
        logger.error("Error: POST /music")

    # GET /music
    r = requests.get(f"{args.u}/music", timeout=args.t)

    if r.ok:
        json_response = r.json()
        logger.info(f"{json_response}")
    else:
        logger.error("Error: GET /music")

    # POST /music/{id}
    r = requests.post(
        f"{args.u}/music/{eval_music_id}", json=sample(tracks, randint(1, 4)), headers={"Content-Type": "application/json"}, timeout=args.t
    )

    if r.ok:
        logger.info(f"{json_response}")
    else:
        logger.error("Error: POST /music/{eval_music_id}")

    # GET /music/{id}
    done = False
    progressbar(0)
    while not done:
        time.sleep(3)
        r = requests.get(f"{args.u}/music/{eval_music_id}", timeout=args.t)
        if r.ok:
            json_response = r.json()
            progress = json_response["progress"]
            progressbar(progress)
            if progress >= 100:
                done = True
                final_download_url = json_response["final"]
                print("\n")
                logger.info(f"{json_response}")
        else:
            logger.error("Error: GET /music/{eval_music_id}")

    # Download final music
    r = requests.get(final_download_url)
    if r.ok:
        with open("final.wav", "wb") as f:
            f.write(r.content)
    else:
        logger.error("Error: GET {final_download_url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split an audio track", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-u", type=str, help="API URL", default="http://localhost:7123")
    parser.add_argument("-t", type=int, help="Request Timeout", default=3)
    args = parser.parse_args()

    main(args)
