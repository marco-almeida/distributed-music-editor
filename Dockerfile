FROM python:3.11-slim-bullseye

# 
WORKDIR /code

# 
COPY ./requirements_torch.txt /code/requirements_torch.txt
COPY ./requirements_api.txt /code/requirements_api.txt
COPY ./requirements_demucs.txt /code/requirements_demucs.txt


# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg build-essential

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements_torch.txt && \
    pip install --no-cache-dir --upgrade -r /code/requirements_api.txt && \
    pip install --no-cache-dir --upgrade -r /code/requirements_demucs.txt

# 
COPY ./src /code/src

WORKDIR /code/src

# Create the directory and set permissions
RUN mkdir -p /tmp/distributed-music-editor && chmod -R 777 /tmp/distributed-music-editor

#
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]

