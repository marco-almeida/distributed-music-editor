import os
import shutil

from pydub import AudioSegment

music_counter = 0
track_counter = 0


def get_music_id():
    global music_counter
    ctr = music_counter
    music_counter = music_counter + 1
    return ctr


def get_track_id():
    global track_counter
    ctr = track_counter
    track_counter = track_counter + 1
    return ctr


def split_mp3(input_file, chunk_length):
    audio = AudioSegment.from_file(input_file, format="mp3")

    # Calculate the total duration of the audio file
    total_duration = len(audio)

    # Calculate the number of chunks based on the chunk length provided
    num_chunks = total_duration // chunk_length

    # Split the audio into chunks
    chunks = [audio[i * chunk_length : (i + 1) * chunk_length] for i in range(num_chunks)]

    # Add the remaining portion as the last chunk if it exists
    if total_duration % chunk_length != 0:
        remaining_chunk = audio[num_chunks * chunk_length :]
        chunks.append(remaining_chunk)

    return chunks


def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
    except Exception as e:
        pass
