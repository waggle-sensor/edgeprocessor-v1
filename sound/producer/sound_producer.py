#!/usr/bin/env python3

import glob
import queue
import threading
import json
import pika
import logging
import pyaudio
import time
import wave

# The module should be moved to an appropriate location for both image and sound
import sys
sys.path.append('../../image')
# sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

class RPCListener(object):
    def __init__(self):
        self.requests = queue.Queue()

    def open(self, listening_queue):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.queue = self.channel.queue_declare(listening_queue, exclusive=True)

    def close(self):
        self.connection.close()

    def read(self):
        if self.requests.empty():
            return None
        return self.requests.get()

    def listen(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()

    def on_request(self, ch, method, props, body):
        try:
            message = json.loads(body.decode())
            self.requests.put(message)
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body='Ok')
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as ex:
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=str(ex))
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        try:
            self.channel.basic_consume(self.on_request, queue=self.queue)
            self.channel.start_consuming()
        except:
            self.channel.stop_consuming()


def interpret_request(request):
    reference = command = duration = None
    if 'reference' in request:
        reference = request['reference']

    if 'command' in request:
        command = request['command']

    if 'duration' in request:
        duration = request['duration']

    return reference, command, duration

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # microphones = glob.glob('/dev/waggle_microphone*')
    microphones = [2]
    if len(microphones) == 0:
        raise Exception('no available microphones detected')

    rpc_listener = RPCListener()
    try:
        rpc_listener.open('audio_rpc')
        rpc_listener.listen()
    except Exception as ex:
        logging.error('Could not set up RPC: %s' % (str(ex)))
        exit(-1)

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='sound_pipeline', type='direct')

    while True:
        request = rpc_listener.read()
        if request is None:
            time.sleep(0.1)
            continue

        if not isinstance(request, dict):
            logging.error('Could not interpret the request: %s is not dictionary' % (str(request),))
            continue
        request = []
        reference, command, duration = interpret_request(request)
        logging.info('%s requested %s for %d' % (reference, command, duration))

        audio = pyaudio.PyAudio()
        stream = audio.open(input_device_index=microphones[0],
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK)

        frames = []

        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        packet = Packet()
        packet.meta_data = { 'node_id': '00000',
                             'device': os.path.basename(microphone[0]),
                             'producer': os.path.basename(__file__),
                             'datetime': time.time()}
        packet.raw = frames
        channel.basic_publish(
            exchange='sound_pipeline',
            routing_key=reference,
            body=packet.output())

if __name__ == '__main__':
    main()