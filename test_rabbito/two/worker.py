import pika
import torch
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio
from demucs.pretrained import get_model
from pydub import AudioSegment


def deep_process_music(input_file_path, output_path):
    # limit the number of thread used by pytorch
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


connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()

channel.queue_declare(queue="task_queue", durable=True)
print(" [*] Waiting for messages. To exit press CTRL+C")


def process_callback(ch, method, properties, body):
    print(" [x] Received %r. Processing..." % (body.decode()))
    deep_process_music(
        "/tmp/distributed-music-editor/originals/" + body.decode() + ".mp3", "/tmp/distributed-music-editor/processed/" + body.decode()
    )
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue="task_queue", on_message_callback=process_callback)

channel.start_consuming()
