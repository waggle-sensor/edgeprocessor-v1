#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license

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
import os

import traceback

# The module should be moved to an appropriate location for both image and sound
import sys
sys.path.append('../../image')
# sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

datetime_format = '%a %b %d %H:%M:%S %Z %Y'

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

        self.data = []
        # Because the first one or two seconds of recording
        # gets noise like cranky sounds, a recording should always be
        # 2 seconds shifted to avoid saving that cranky sounds.
        self.MAGIC_SKIP_SECONDS = 2

    def connect(self, device):
        self.device = device
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            input_device_index=device,
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            # frames_per_buffer=self.CHUNK,
            stream_callback=self.callback)
        self.stream.stop_stream()

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
        self.jobs[str(uuid.uuid4())] = [orderer, [], time.time(), time.time() + duration + self.MAGIC_SKIP_SECONDS]

    def get(self):
        if self.jobs_done.empty():
            return None
        return self.jobs_done.get()

    def callback(self, in_data, frame_count, time_info, status):
        self.data.extend(in_data)
        # print(frame_count)
        # print(time_info)
        # print(len(in_data))
        # print(len(self.data))
        # print('---------------------')
        return (in_data, pyaudio.paContinue)

    def run(self):
        while self.thread_alive:
            try:
                if len(self.jobs) > 0:
                    self.data = []
                    # for i in range(0, int(self.RATE / self.CHUNK)):
                    #     data.append(self.stream.read(self.CHUNK))
                    self.stream.start_stream()

                    time.sleep(1)

                    self.stream.stop_stream()

                    done = []
                    for job_id in self.jobs:
                        orderer, buffer, start_time, end_time = self.jobs[job_id]

                        current_time = time.time()
                        # ISSUE: first two seconds of an audio stream has
                        # cranky sound
                        if int(abs(current_time - start_time)) < self.MAGIC_SKIP_SECONDS:
                            continue
                        if current_time < end_time:
                            buffer.extend(self.data)
                        else:
                            done.append(job_id)
                        self.jobs[job_id] = [orderer, buffer, start_time, end_time]

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

def open_pipeline_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.exchange_declare(exchange='sound_pipeline', exchange_type='direct')
    return channel

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

    pipeline = open_pipeline_connection()

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
                reference, data, start_time, end_time = job_done
                packet = Packet()
                packet.meta_data = { 'node_id': '00000',
                                     'device': os.path.basename('/dev/waggle_microphone'),
                                     'producer': os.path.basename(__file__),
                                     'datetime': time.strftime(datetime_format, time.gmtime())}
                packet.raw = bytearray(data)
                if pipeline.is_closed():
                    pipeline = open_pipeline_connection()

                pipeline.basic_publish(
                    exchange='sound_pipeline',
                    routing_key=reference,
                    body=packet.output())
                logger.info('Recorded audio is sent to %s' % (reference,))
            
            time.sleep(0.1)
    except Exception as ex:
        logger.error(str(ex))
        logger.error(traceback.print_tb())
    except KeyboardInterrupt:
        pass

    logger.info('Closing threads...')
    collector.close()
    rpc_listener.close()
    logger.info('Producer terminated')

if __name__ == '__main__':
    main()
