import os
from time import time
from typing import List

import torch
from celery import Celery, chord
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model
from pydub import AudioSegment

from routers.utils import delete_folder

torch.set_num_threads(1)
app = Celery("celery_tasks.tasks", backend="redis://localhost", broker="pyamqp://guest@localhost//")


@app.task
def merge_chunks(*task_ids: List[str]):
    print(f"Ready to do something with {task_ids}")


@app.task
def dispatch_process_music(music_id: int, tracks: List[str], chunk_length: int):
    ROOT = "/tmp/distributed-music-editor"
    split_mp3(f"{ROOT}/originals/{music_id}.mp3", f"{ROOT}/chunks/{music_id}", chunk_length)

    try:
        delete_folder(f"{ROOT}/pre_processing/{music_id}")
    except:
        pass
    os.makedirs(f"{ROOT}/pre_processing/{music_id}")

    task_ids = []

    for idx, chunk in enumerate(os.listdir(f"{ROOT}/chunks/{music_id}")):
        task = process_chunks.s(f"{ROOT}/chunks/{music_id}/{chunk}", f"{ROOT}/pre_processing/{music_id}", idx)
        task_ids.append(task)

    callback_task = merge_chunks.s(task_ids)

    chord(task_ids)(callback_task)


@app.task
def process_chunks(chunk_path: str, output_folder: str, idx: int):
    model = get_model(name="htdemucs")
    model.cpu()
    model.eval()

    wav = AudioFile(chunk_path).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    sources = apply_model(model, wav[None], device="cpu", progress=True, num_workers=1)[0]
    sources = sources * ref.std() + ref.mean()

    for source, name in zip(sources, model.sources):
        stem = f"{output_folder}/{name}_{idx}.wav"
        save_audio(source, str(stem), samplerate=model.samplerate)


@app.task
def deep_process_music(music_id: int, tracks: List[str]):
    start_time = time()

    ROOT = "/tmp/distributed-music-editor"
    original_file = f"{ROOT}/originals/{music_id}.mp3"
    OUTPUT_DIR = f"{ROOT}/processed/{music_id}"

    if os.path.exists(OUTPUT_DIR):
        mix_tracks(OUTPUT_DIR, tracks)
        return time() - start_time
    else:
        os.makedirs(OUTPUT_DIR)

    model = get_model(name="htdemucs")
    model.cpu()
    model.eval()

    wav = AudioFile(original_file).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    sources = apply_model(model, wav[None], device="cpu", progress=True, num_workers=1)[0]
    sources = sources * ref.std() + ref.mean()

    for source, name in zip(sources, model.sources):
        stem = f"{OUTPUT_DIR}/{name}.wav"
        save_audio(source, str(stem), samplerate=model.samplerate)

    mix_tracks(OUTPUT_DIR, tracks)
    return time() - start_time


def mix_tracks(input_dir: str, tracks: List[str]):
    track = AudioSegment.from_wav(f"{input_dir}/{tracks[0]}.wav")
    for idx in range(1, len(tracks)):
        track = track.overlay(AudioSegment.from_wav(f"{input_dir}/{tracks[idx]}.wav"), position=0)
    track.export(f"{input_dir}/final.wav", format="wav")


def split_mp3(input_file, output_folder, chunk_length):
    audio = AudioSegment.from_file(input_file, format="mp3")
    total_duration = len(audio)
    num_chunks = total_duration // chunk_length
    delete_folder(output_folder)
    os.makedirs(output_folder)

    for i in range(num_chunks):
        audio[i * chunk_length : (i + 1) * chunk_length].export(f"{output_folder}/{i}.mp3", format="mp3")

    if total_duration % chunk_length != 0:
        audio[num_chunks * chunk_length :].export(f"{output_folder}/{num_chunks}.mp3", format="mp3")
