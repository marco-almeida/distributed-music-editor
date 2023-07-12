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


def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
    except Exception as e:
        pass
