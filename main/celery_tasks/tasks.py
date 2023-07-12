import os
from time import time
from typing import List

from celery import shared_task
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model
from pydub import AudioSegment


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    name="music_processing:deep_process_music",
)
def deep_process_music(self, music_id: int, tracks: List[str]):
    start_time = time()
    # limit the number of thread used by pytorch
    import torch

    torch.set_num_threads(1)

    ROOT = "/tmp/distributed-music-editor"
    original_file = f"{ROOT}/originals/{music_id}.mp3"
    OUTPUT_DIR = f"{ROOT}/processed/{music_id}"
    # if processed folder already exists, just do the mixing part
    if os.path.exists(OUTPUT_DIR):
        # load the tracks to merge them
        mix_tracks(OUTPUT_DIR, tracks)
        return time() - start_time
    else:
        os.makedirs(OUTPUT_DIR)
    # get the model
    model = get_model(name="htdemucs")
    model.cpu()
    model.eval()

    # load the audio file
    wav = AudioFile(original_file).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    # apply the model
    sources = apply_model(model, wav[None], device="cpu", progress=True, num_workers=1)[0]
    sources = sources * ref.std() + ref.mean()

    # store the model
    for source, name in zip(sources, model.sources):
        stem = f"{OUTPUT_DIR}/{name}.wav"
        save_audio(source, str(stem), samplerate=model.samplerate)

    # load the tracks to merge them
    mix_tracks(OUTPUT_DIR, tracks)
    return time() - start_time


def mix_tracks(input_dir: str, tracks: List[str]):
    # load the tracks to merge them
    track = AudioSegment.from_wav(f"{input_dir}/{tracks[0]}.wav")
    for idx in range(1, len(tracks)):
        track = track.overlay(AudioSegment.from_wav(f"{input_dir}/{tracks[idx]}.wav"), position=0)
    # merge audio
    track.export(f"{input_dir}/final.wav", format="wav")
