# Distributed Music Editor

This app enables users to split songs into distinct parts, such as vocals, drums, and more, allowing for customized versions, such as karaoke. Built with **FastAPI**, the app provides a **RESTful API** for submission and processing of .mp3 files. Utilizing the [demucs](https://github.com/facebookresearch/demucs) library with a deep learning model, tracks are separated into individual components. The **Celery** module handles processing by dividing the work into multiple jobs, all conveniently monitored through the API. RabbitMQ is used to distribute the work among multiple workers and Redis stores the results of the work.

All work is done asynchronously and as simultaneously as possible.

## Set Up

### Set Up with Docker

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

```bash
sudo apt install ffmpeg
sudo apt install rabbitmq-server
sudo apt install redis

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

In case of celery workers shutting down unexpectedly, add the argument --autoscale=max,min e.g --autoscale=4,2. Make this change in the entrypoint.sh file too if using docker.

> The autoscaler component is used to dynamically resize the pool based on load

## Documentation

Postman collection and environment available in the root directory. API documentation based on OpenAPI available in `/docs` endpoint.

## License

This project is licensed under the MIT License.
