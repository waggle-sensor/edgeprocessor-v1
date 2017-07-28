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
import uuid

# The module should be moved to an appropriate location for both image and sound
import sys
sys.path.append('../../image')
# sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

class RPCListener(object):
    def __init__(self, logger=None):
        self.requests = queue.Queue()
        self.thread_alive = False
        self.logger = logger

    def open(self, listening_queue=None):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        if listening_queue is not None:
            self.channel.queue_declare(queue=listening_queue, exclusive=True)
            self.queue = listening_queue

    def close(self):
        self.thread_alive = False
        self.thread.join()
        self.connection.close()

    def read(self):
        if self.requests.empty():
            return None
        return self.requests.get()

    def listen(self):
        self.thread = threading.Thread(target=self.run)
        self.thread_alive = True
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
        while self.thread_alive:
            try:
                method, header, body = self.channel.basic_get(queue=self.queue)
                if method is not None:
                    if isinstance(method, pika.spec.Basic.GetOk):
                        self.on_request(self.channel, method, header, body)
                time.sleep(0.01)
            except pika.exceptions.ConnectionClosed as ex:
                if self.logger is not None:
                    self.logger.info('RabbitMQ connection closed %s' % (str(ex),))
                    self.logger.info('Restarting RabbitMQ consumption in 5 seconds...')
                time.sleep(5)
                self.open()
            except Exception as ex:
                if self.logger is not None:
                    self.logger.info('RabbitMQ consumption failed %s' % (str(ex),))
                    self.logger.info('Restarting RabbitMQ consumption in 5 seconds...')
                time.sleep(5)


class SoundCollector(object):
    def __init__(self, logger):
        self.logger = logger
        self.config = {}
        self.thread_alive = False
        self.jobs = {}
        self.jobs_done = queue.Queue()

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS=  2
        self.RATE = 48000

    def connect(self, device):
        self.device = device
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            input_device_index=device,
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK)

    def open(self, device):
        self.connect(device)
        self.thread = threading.Thread(target=self.run)
        self.thread_alive = True
        self.thread.start()

    def close(self):
        self.thread_alive = False
        self.thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def put(self, orderer, duration):
        self.jobs[str(uuid.uuid4())] = [orderer, [], time.time() + duration]

    def get(self):
        if self.jobs_done.empty():
            return None
        return self.jobs_done.get()

    def run(self):
        while self.thread_alive:
            try:
                if len(self.jobs) > 0:
                    data = []
                    for i in range(0, int(self.RATE / self.CHUNK)):
                        data = self.stream.read(self.CHUNK)

                    done = []
                    for job_id in self.jobs:
                        orderer, buffer, end_time = self.jobs[job_id]

                        current_time = time.time()
                        if current_time < end_time:
                            buffer.append(data)
                        else:
                            done.append(job_id)
                        self.jobs[job_id] = [orderer, buffer, end_time]

                    for job_id in done:
                        self.jobs_done.put(self.jobs.pop(job_id))
                else:
                    time.sleep(1)
            except (OSError, IOError) as ex:
                logger.error('%s' % (str(ex),))
                logger.info('Restaring audio stream in 3 seconds...')
                time.sleep(3)
                self.connect(self.device)
            except Exception as ex:
                logger.error('%s %s' % (str(ex), type(ex)))



def interpret_request(request):
    reference = command = duration = None
    if 'reference' in request:
        reference = request['reference']

    if 'command' in request:
        command = request['command']

    if 'duration' in request:
        duration = request['duration']

    return reference, command, duration


def main():
    # microphones = glob.glob('/dev/waggle_microphone*')
    microphones = [2]
    if len(microphones) == 0:
        raise Exception('no available microphones detected')

    rpc_listener = RPCListener(logger)
    try:
        rpc_listener.open('audio_rpc')
        rpc_listener.listen()
    except Exception as ex:
        logger.error('Could not set up RPC: %s' % (str(ex)))
        exit(-1)

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='sound_pipeline', type='direct')

    collector = SoundCollector(logger)
    collector.open(microphones[0])

    try:
        while True:
            request = rpc_listener.read()
            if request is not None:
                if isinstance(request, dict):
                    reference, command, duration = interpret_request(request)
                    logger.info('%s requested %s for %d' % (reference, command, duration)) 
                    # TODO: add commands.....
                    collector.put(reference, duration)
                else:
                    logger.error('Could not interpret the request: %s is not dictionary' % (str(request),))
            
            job_done = collector.get()
            if job_done is not None:
                reference = job_done[0]
                data = job_done[1]
                packet = Packet()
                packet.meta_data = { 'node_id': '00000',
                                     'device': os.path.basename(microphone[0]),
                                     'producer': os.path.basename(__file__),
                                     'datetime': time.time()}
                packet.raw = data
                channel.basic_publish(
                    exchange='sound_pipeline',
                    routing_key=reference,
                    body=packet.output())
            
            time.sleep(0.1)
    except Exception as ex:
        logger.error(str(ex))
    except KeyboardInterrupt:
        pass

    logger.info('Closing threads...')
    collector.close()
    rpc_listener.close()
    logger.info('Producer terminated')

if __name__ == '__main__':
    main()
