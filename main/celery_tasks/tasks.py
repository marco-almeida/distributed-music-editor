import os
from time import time
from typing import List

import torch
from celery import Celery, chord
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model
from pydub import AudioSegment
from pydub.utils import make_chunks

from routers.utils import delete_folder

torch.set_num_threads(1)
app = Celery("celery_tasks.tasks", backend="redis://localhost", broker="pyamqp://guest@localhost//")


@app.task
def merge_chunks(ignore, *stuff):
    music_id: int = stuff[0]
    tracks: List[str] = stuff[1]

    chunked_channels = {"bass": [], "drum": [], "othe": [], "voca": []}
    ROOT = "/tmp/distributed-music-editor"
    for channel in os.listdir(f"{ROOT}/pre_processing/{music_id}"):
        chunked_channels[channel[0:4]].append(f"{ROOT}/pre_processing/{music_id}/{channel}")

    # for each channel, load all chunks into memory and append them
    final = {"bass": AudioSegment.empty(), "drums": AudioSegment.empty(), "other": AudioSegment.empty(), "vocals": AudioSegment.empty()}

    delete_folder(f"{ROOT}/processed/{music_id}")
    os.makedirs(f"{ROOT}/processed/{music_id}")
    for channel in final.keys():
        # for each list, sort it alphanumerically
        chunked_channels[channel[0:4]].sort()
        # for each channel, append the chunks
        for chunk in chunked_channels[channel[0:4]]:
            # load to memory and append
            final[channel] += AudioSegment.from_wav(chunk)
        file_name = hash(f"{music_id}|{channel}")
        final[channel].export(f"{ROOT}/processed/{music_id}/{channel}.wav", format="wav")

    # export final track according to user's choice
    mix_tracks(f"{ROOT}/processed/{music_id}", tracks)


@app.task
def dispatch_process_music(music_id: int, tracks: List[str], chunk_length: int):
    ROOT = "/tmp/distributed-music-editor"
    splice_music(f"{ROOT}/originals/{music_id}.mp3", f"{ROOT}/chunks/{music_id}", chunk_length)

    delete_folder(f"{ROOT}/pre_processing/{music_id}")
    os.makedirs(f"{ROOT}/pre_processing/{music_id}")

    task_ids = []

    for idx, chunk in enumerate(os.listdir(f"{ROOT}/chunks/{music_id}")):
        task = process_chunks.s(f"{ROOT}/chunks/{music_id}/{chunk}", f"{ROOT}/pre_processing/{music_id}", idx)
        task_ids.append(task)

    print(f"aqui tenho {music_id} e {tracks}")
    callback_task = merge_chunks.s(music_id, tracks)

    chord(task_ids)(callback_task)
    return task_ids


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


def splice_music(input_file, output_folder, chunk_length):
    audio_segment = AudioSegment.from_file(input_file)
    chunks = make_chunks(audio_segment, chunk_length)

    delete_folder(output_folder)
    os.makedirs(output_folder)
    for i in range(len(chunks)):
        chunks[i].export(f"{output_folder}/{i}.mp3", format="mp3")
