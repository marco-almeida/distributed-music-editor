import hashlib
import os
from typing import List

import torch
from celery import Celery, chord
from celery_tasks.utils import mix_tracks, splice_music
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model
from pydub import AudioSegment
from routers.utils import delete_folder, make_dirs

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
        name_to_be_hashed = f"{music_id}|{channel}".encode()
        file_name = int(hashlib.md5(name_to_be_hashed).hexdigest(), 16)
        final[channel].export(f"{ROOT}/processed/{file_name}.wav", format="wav")
        final[channel] = file_name

    # export final track according to user's choice
    mix_tracks(music_id, final, tracks)


@app.task
def dispatch_process_music(music_id: int, tracks: List[str], chunk_length: int):
    splice_music(f"{ROOT}/originals/{music_id}.mp3", f"{ROOT}/chunks/{music_id}", chunk_length)

    delete_folder(f"{ROOT}/pre_processing/{music_id}")
    make_dirs(f"{ROOT}/pre_processing/{music_id}")

    task_sigs = []

    for idx, chunk in enumerate(os.listdir(f"{ROOT}/chunks/{music_id}")):
        task = process_chunks.s(f"{ROOT}/chunks/{music_id}/{chunk}", f"{ROOT}/pre_processing/{music_id}", idx)
        task_sigs.append(task)

    callback_task = merge_chunks.s(music_id, tracks)

    chord(task_sigs)(callback_task)


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
