#!/usr/bin/env python3

import time
import json
import base64
import pika
import queue
import threading

class Packet(object):
    META = 'meta_data'
    RESULTS = 'results'
    RAW = 'raw'
    def __init__(self, binary_packet=None):
        self.meta_data = {}
        self.data = []
        self.raw = None
        if binary_packet is not None:
            self.load(binary_packet)

    def load(self, binary_packet):
        packet = json.loads(binary_packet)
        self.meta_data = packet[self.META]
        self.data = packet[self.RESULTS]
        self.raw = self.decode_raw(packet[self.RAW])

    def output(self):
        message = {self.META: self.meta_data, self.RESULTS: self.data, self.RAW: self.encode_raw(self.raw).decode()}
        return json.dumps(message)

    def decode_raw(self, base64_raw):
        return base64.b64decode(base64_raw)

    def encode_raw(self, raw):
        return base64.b64encode(raw)


class Streamer(object):
    def __init__(self):
        pass

    def open(self, **args):
        raise NotImplemented('Open function should be implemented')

    def read(self):
        raise NotImplemented('Read function should be implemented')

    def write(self, data, **args):
        raise NotImplemented('Write function should be implemented')

    def run(self):
        raise NotImplemented('Must have run method')

class RabbitMQStreamer(Streamer):
    def __init__(self, logger=None):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.routing_in = None
        self.routing_out = None
        self.queue = None
        self.logger = logger
        self.listener = None
        self.last_message = None

    def open(self, **args):
        pass

    def close(self):
        self.ls_alive = False
        if self.listener is not None:
            self.listener.join()
        if self.connection is not None:
            if self.connection.is_open:
                self.connection.close()

    def config(self, input_exchange, routing_key_in='0', routing_key_out=None):
        self.exchange = input_exchange
        self.routing_in = routing_key_in
        self.routing_out = routing_key_out

    def connect(self, host='localhost', input_exchange_declare=True):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            self.channel = self.connection.channel()
            if input_exchange_declare:
                self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct')

            result = self.channel.queue_declare(exclusive=True, arguments={'x-max-length': 1})
            self.queue = result.method.queue
            self.channel.queue_bind(queue=self.queue, exchange=self.exchange, routing_key=self.routing_in)
            self.listener = threading.Thread(target=self.run)
            self.is_alive = True
            self.listener.start()
        except Exception as ex:
            return False, str(ex)
        return True, ''

    def read(self):
        if self.last_message is not None:
            return True, Packet(self.last_message)
        else:
            return False, ''
        
    def write(self, data):
        try:
            self.channel.basic_publish(exchange=self.exchange, routing_key=self.routing_out, body=data)
            return True
        except Exception as ex:
            if self.logger:
                self.logger.error('Could not write %s: %s' % (str(data), str(ex)))
            return False

    def run(self):
        while self.is_alive:
            try:
                method, header, body = self.channel.basic_get(queue=self.queue, no_ack=True)
                if method is not None:
                    if isinstance(method, pika.spec.Basic.GetOk):
                        self.last_message = body.decode()
            except pika.exceptions.ConnectionClosed as ex:
                if self.logger is not None:
                    self.logger.info('RabbitMQ connection closed %s' % (str(ex),))
                    self.logger.info('Restarting RabbitMQ consumption in 5 seconds...')
                time.sleep(5)
                self.connect()
            except Exception as ex:
                if self.logger is not None:
                    self.logger.info('RabbitMQ consumption failed %s' % (str(ex),))
                    self.logger.info('Restarting RabbitMQ consumption in 5 seconds...')
                time.sleep(5)
            time.sleep(1)

class Processor(object):
    def __init__(self):
        self.processor = None
        self.input_handler = []
        self.output_handler = []

    def add_handler(self, handler, handler_type='in-out'):
        if 'in' in handler_type:
            self.input_handler.append(handler)
        if 'out' in handler_type:
            self.output_handler.append(handler)

    def run(self):
        raise NotImplmented('Run method should be implemented')
