# Distributed Music Editor

This project uses RabbitMQ, Redis, Celery and FastAPI to develop a system that, through a RESTful API, receives .mp3 files and splits them into multiple tracks/channels, e.g vocals, drums, bass, etc., as to allow the user to for example, separate the vocals from the rest of the track, in order to create a karaoke version of the song.

All work is done asynchronously and as simultaneously as possible.

RabbitMQ is used to distribute the work among multiple workers. Redis is used to store the results of the work and Celery is used to manage the workers. FastAPI is used to develop the API.

The codes uses one library named [demucs](https://github.com/facebookresearch/demucs),
this library uses a deep learning model to separate the tracks.
This library requires [ffmpeg](https://ffmpeg.org/) to work.
It should be present in most Linux distributions.

Code snippet to split a track into multiple tracks provided by professors [mariolpantunes](https://github.com/mariolpantunes), [dgomes](https://github.com/dgomes) and [nunolau](https://github.com/nunolau).

## Set Up

### Set Up with Docker

To run the project with docker, run the following commands:

```bash
cd redis
docker compose up -d
cd ../rabbitmq
docker compose up -d
cd ..
docker build . -t dme-api
docker compose up
```

### Set Up without Docker

## Dependencies

For Ubuntu (and other debian based linux), run the following commands:

```bash
sudo apt install ffmpeg
sudo apt install rabbitmq-server
sudo apt install redis
```

## Setup

Run the following commands to setup the environement:

```bash
python3 -m venv venv
source venv/bin/activate

pip install pip --upgrade
pip install -r requirements_torch.txt
pip install -r requirements_demucs.txt
pip install -r requirements_api.txt

cd src
celery -A celery_tasks.tasks worker --loglevel=INFO &
python3 main.py
```

It is important to install the requirements following the previous instructions.
By default, PyTorch will install the CUDA version of the library (over 4G simple from the virtual environment).
As such, the current instructions force the installation of the CPU version of PyTorch and then installs Demucs.

In case of celery workers shutting down unexpectedly, add the argument --autoscale=4,2. 4 is the maximum number of processes and 2 is the minimum number of processes.

> The autoscaler component is used to dynamically resize the pool based on load

## License

This project is licensed under the MIT License.
