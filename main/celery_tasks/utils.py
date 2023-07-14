import hashlib
from typing import List

from pydub import AudioSegment
from pydub.utils import make_chunks
from routers.utils import delete_folder, make_dirs


def mix_tracks(music_id: int, channel_to_hash: dict, tracks: List[str]):
    final = AudioSegment.from_wav(f"/tmp/distributed-music-editor/processed/{channel_to_hash[tracks[0]]}.wav")
    for idx in range(1, len(tracks)):
        final = final.overlay(AudioSegment.from_wav(f"/tmp/distributed-music-editor/processed/{channel_to_hash[tracks[idx]]}.wav"))
    name_to_be_hashed = f"{music_id}|final".encode()
    file_name = int(hashlib.md5(name_to_be_hashed).hexdigest(), 16)
    final.export(f"/tmp/distributed-music-editor/processed/{file_name}.wav", format="wav")


def splice_music(input_file, output_folder, chunk_length):
    audio_segment = AudioSegment.from_file(input_file)
    chunks = make_chunks(audio_segment, chunk_length)

    delete_folder(output_folder)
    make_dirs(output_folder)
    for i in range(len(chunks)):
        chunks[i].export(f"{output_folder}/{i}.mp3", format="mp3")
