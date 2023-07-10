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
def deep_process_music(self, input_file_path: str, output_path: str):
    # limit the number of thread used by pytorch
    print("\n\n\n\n", input_file_path, output_path, "\n\n\n\n")
    import torch

    torch.set_num_threads(1)
    # get the model
    model = get_model(name="htdemucs")
    model.cpu()
    model.eval()

    # load the audio file
    wav = AudioFile(input_file_path).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()

    # apply the model
    sources = apply_model(model, wav[None], device="cpu", progress=True, num_workers=1)[0]
    sources = sources * ref.std() + ref.mean()

    # store the model
    for source, name in zip(sources, model.sources):
        stem = f"{output_path}/{name}.wav"
        save_audio(source, str(stem), samplerate=model.samplerate)

    # load the vocals and drums to merge them
    vocals = AudioSegment.from_wav(f"{output_path}/vocals.wav")
    drums = AudioSegment.from_wav(f"{output_path}/drums.wav")
    # merge audio
    # audio = vocals + drums
    audio = vocals.overlay(drums, position=0)
    # store the merged audio
    audio.export(f"{output_path}/merged.wav", format="wav")
