#!/usr/bin/env python3

import pika
import json
import queue
import numpy as np
import logging
import uuid

import sys
sys.path.append('../../image')
from processor import *

class RPCRequester(object)
    def __init__(self, my_routing_key):
        self.my_routing_key = my_routing_key
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='audio_rpc', exclusive=True)
        self.callback_queue = self.channel.queue_declare(exclusive=True).method.queue
        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def request(self, duration):
        response = None
        self.corr_id = str(uuid.uuid4())
        message = {'reference': my_routing_key, 'command':'read', 'duration':duration}
        channel.basic_publish(
            exchange='',
            routing_key='audio_rpc',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id),
            body=json.dumps(message.encode()))

        while response is None:
            self.connection.process_data_events()
        return self.response

def get_rmq_pipeline(routing_key, pipeline_exchange='sound_pipeline'):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=pipeline_exchange, type='direct')
    result = channel.queue_declare(exclusive=True)
    channel.queue_bind(queue=result.method.queue, exchange=pipeline_exchange, routing_key=routing_key)
    return channel





def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    my_routing_key = '1'

    rpc = get_rmq_rpc()
    my_rpc_queue = rpc.queue_declare(exclusive=True).method.queue
    pipeline = get_rmq_pipeline(my_routing_key)
    
    logging.info('Request sample')
    result = request(rpc, my_rpc_queue)
    if 'OK' in result:
        

    
if __name__ == '__main__':
    main()