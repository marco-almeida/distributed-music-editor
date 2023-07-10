import time
from random import randrange
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()

channel.queue_declare(queue="task_queue", durable=True)
print(" [*] Waiting for messages. To exit press CTRL+C")


def callback(ch, method, properties, body):
    processing_time = randrange(5)
    print(" [x] Received %r. Processing for %d seconds" % (body.decode(), processing_time))
    time.sleep(processing_time)
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue="task_queue", on_message_callback=callback)

channel.start_consuming()
