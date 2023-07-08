# coding: utf-8

__author__ = "Mário Antunes"
__version__ = "1.0"
__email__ = "mario.antunes@ua.pt"
__status__ = "Production"
__license__ = "MIT"

import argparse
import logging

# limit the number of thread used by pytorch
import torch
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model
from pydub import AudioSegment

torch.set_num_threads(1)


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main(args):
    # get the model
    model = get_model(name="htdemucs")
    model.cpu()
    model.eval()

    # load the audio file
    wav = AudioFile(args.i).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    # apply the model
    sources = apply_model(model, wav[None], device="cpu", progress=True, num_workers=1)[0]
    sources = sources * ref.std() + ref.mean()
    print(sources)

    # store the model
    for source, name in zip(sources, model.sources):
        stem = f"{args.o}/{name}.wav"
        save_audio(source, str(stem), samplerate=model.samplerate)

    # load the vocals and drums to merge them
    vocals = AudioSegment.from_wav("tracks/vocals.wav")
    drums = AudioSegment.from_wav("tracks/drums.wav")
    # merge audio
    # audio = vocals + drums
    audio = vocals.overlay(drums, position=0)
    # store the merged audio
    audio.export("merged.wav", format="wav")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split an audio track", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, help="input mp3", default="music.mp3")
    parser.add_argument("-o", type=str, help="output folder", default="tracks")
    args = parser.parse_args()

    main(args)
