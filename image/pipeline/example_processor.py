import pika
import json
import cv2
import numpy as np

import sys
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

EXCHANGE = 'image_pipeline'
ROUTING_KEY_RAW = '0'
ROUTING_KEY_OUT = '1'
ROUTING_KEY_EXPORT = '9'

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

result = channel.queue_declare(exclusive=True)
my_queue = result.method.queue


def get_average_color(image):
    try:
        # if isinstance(image_file_path, bytes):
        #     image_file_path = image_file_path.decode()

        nparr_img = np.fromstring(image, np.uint8)
        img = cv2.imdecode(nparr_img, cv2.IMREAD_COLOR)

        avg_color = np.average(img, axis=0)
        return np.average(avg_color, axis=0)
    except Exception as ex:
        print(ex)


def on_process(ch, method, props, body):
    try:
        message = Packet(body.decode())

        # Calculate average color of the image
        avg_color = str(get_average_color(message.raw))
        results = message.data.append({'avg_color': avg_color})

        # Export the image along with the information
        channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY_EXPORT, body=message.output())
    except Exception as ex:
        print(ex)

channel.queue_bind(queue=my_queue, exchange=EXCHANGE, routing_key=ROUTING_KEY_RAW)

channel.basic_consume(on_process, queue=my_queue, no_ack=True)
try:
    channel.start_consuming()
except:
    channel.stop_consuming()