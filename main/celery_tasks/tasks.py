import ctypes
import os
from time import time
from typing import List

import torch
from celery import Celery, chord
from celery.result import AsyncResult
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model
from pydub import AudioSegment
from pydub.utils import make_chunks

from routers.utils import delete_folder

torch.set_num_threads(1)
app = Celery("celery_tasks.tasks", backend="redis://localhost", broker="pyamqp://guest@localhost//")

ROOT = "/tmp/distributed-music-editor"


@app.task
def merge_chunks(ignore, *stuff):
    music_id: int = stuff[0]
    tracks: List[str] = stuff[1]

    chunked_channels = {"bass": [], "drum": [], "othe": [], "voca": []}
    for channel in os.listdir(f"{ROOT}/pre_processing/{music_id}"):
        chunked_channels[channel[0:4]].append(f"{ROOT}/pre_processing/{music_id}/{channel}")

    # for each channel, load all chunks into memory and append them
    final = {"bass": AudioSegment.empty(), "drums": AudioSegment.empty(), "other": AudioSegment.empty(), "vocals": AudioSegment.empty()}

    for channel in final.keys():
        # for each list, sort it alphanumerically
        chunked_channels[channel[0:4]].sort()
        # for each channel, append the chunks
        for chunk in chunked_channels[channel[0:4]]:
            # load to memory and append
            final[channel] += AudioSegment.from_wav(chunk)
        file_name = ctypes.c_size_t(hash(f"{music_id}|{channel}")).value
        final[channel].export(f"{ROOT}/processed/{file_name}.wav", format="wav")
        final[channel] = file_name

    print(f"final: {final}")

    # export final track according to user's choice
    mix_tracks(music_id, final, tracks)


@app.task
def dispatch_process_music(music_id: int, tracks: List[str], chunk_length: int):
    splice_music(f"{ROOT}/originals/{music_id}.mp3", f"{ROOT}/chunks/{music_id}", chunk_length)

    delete_folder(f"{ROOT}/pre_processing/{music_id}")
    os.makedirs(f"{ROOT}/pre_processing/{music_id}")

    task_ids = []

    for idx, chunk in enumerate(os.listdir(f"{ROOT}/chunks/{music_id}")):
        task = process_chunks.s(f"{ROOT}/chunks/{music_id}/{chunk}", f"{ROOT}/pre_processing/{music_id}", idx)
        task_ids.append(task)

    print(f"aqui tenho {music_id} e {tracks}")
    callback_task = merge_chunks.s(music_id, tracks)

    bababooey = chord(task_ids)(callback_task)
    print(bababooey)
    print(type(bababooey))
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


def mix_tracks(music_id: int, channel_to_hash: dict, tracks: List[str]):
    final = AudioSegment.from_wav(f"/tmp/distributed-music-editor/processed/{channel_to_hash[tracks[0]]}.wav")
    for idx in range(1, len(tracks)):
        final = final.overlay(AudioSegment.from_wav(f"/tmp/distributed-music-editor/processed/{channel_to_hash[tracks[idx]]}.wav"))
    file_name = ctypes.c_size_t(hash(f"{music_id}|final")).value
    final.export(f"/tmp/distributed-music-editor/processed/{file_name}.wav", format="wav")

    print(ctypes.c_size_t(hash(f"{music_id}|final")).value)


def splice_music(input_file, output_folder, chunk_length):
    audio_segment = AudioSegment.from_file(input_file)
    chunks = make_chunks(audio_segment, chunk_length)

    delete_folder(output_folder)
    os.makedirs(output_folder)
    for i in range(len(chunks)):
        chunks[i].export(f"{output_folder}/{i}.mp3", format="mp3")
