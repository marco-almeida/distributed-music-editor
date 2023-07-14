import os
import shutil

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


def delete_folder(*folder_path):
    try:
        for folder in folder_path:
            shutil.rmtree(folder)
    except Exception as e:
        pass


def make_dirs(*folder_path):
    try:
        for folder in folder_path:
            os.makedirs(folder, exist_ok=True)
    except Exception as e:
        pass
