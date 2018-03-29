#!/usr/bin/env python3

import time
import json
import base64
import pika
import queue
import threading

class RabbitMQStreamer(Streamer):
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.routing_in = None
        self.routing_out = None
        self.queue = None
        self.listener = None
        self.last_message = None
        self.out_queue = queue.Queue()

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
            packet = Packet(self.last_message)
            self.last_message = None
            return True, packet
        else:
            return False, ''
        
    def write(self, data):
        self.out_queue.put(data)

    def run(self):
        while self.is_alive:
            # Flush any pending messages
            while not self.out_queue.empty():
                data = self.out_queue.get()
                try:
                    self.channel.basic_publish(exchange=self.exchange, routing_key=self.routing_out, body=data)
                except Exception as ex:
                    print('Could not write %s: %s' % (str(data), str(ex)))
                    break

            # Handle any incoming messages
            try:
                method, header, body = self.channel.basic_get(queue=self.queue, no_ack=True)
                if method is not None:
                    if isinstance(method, pika.spec.Basic.GetOk):
                        self.last_message = body.decode()
            except pika.exceptions.ConnectionClosed as ex:
                print('RabbitMQ connection closed %s' % (str(ex),))
                print('Restarting RabbitMQ consumption in 5 seconds...')
                time.sleep(5)
                self.connect()
            except Exception as ex:
                print('RabbitMQ consumption failed %s' % (str(ex),))
                print('Restarting RabbitMQ consumption in 5 seconds...')
                time.sleep(5)
            time.sleep(1)


class Processor(object):
    def __init__(self):
        self.processor = None
        self.input_handler = {}
        self.output_handler = {}

    def add_handler(self, handler, handler_name, handler_type='in-out'):
        if 'in' in handler_type:
            self.input_handler[handler_name] = handler
        if 'out' in handler_type:
            self.output_handler[handler_name] = handler

    def run(self):
        raise NotImplmented('Run method should be implemented')
