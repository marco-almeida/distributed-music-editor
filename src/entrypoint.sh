#!/bin/bash

celery -A celery_tasks.tasks worker --loglevel=INFO --uid=nobody --gid=nogroup &
python3 main.py
