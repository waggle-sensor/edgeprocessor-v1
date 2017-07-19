#!/usr/bin/env python3

import os
import pika
import json
import cv2
import numpy as np
import time
import argparse
import sys
import logging
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

datetime_format = '%a %b %d %H:%M:%S %Z %Y'

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


class ImageCollectionProcessor(Processor):
    def __init__(self):
        super().__init__()
        self.options = {
        'start_time': time.time(),
        'end_time': time.time(),
        'daytime': True,
        'interval': 1,
        'verbose': False
        }

    def setValues(self, options):
        self.options.update(options)

    def read(self):
        for stream in self.input_handler:
            if stream is None:
                return False, None
            return stream.read()

    def write(self, packet):
        for stream in self.output_handler:
            if stream is None:
                return False
            stream.write(packet.output())
            if self.options['verbose']:
                logger.info('A packet is sent to output')

    def run(self):
        while time.time() <= self.options['start_time']:
            time.sleep(1)

        try:
            last_updated_time = time.time()
            while True:
                current_time = time.time()
                if current_time - last_updated_time > self.options['interval']:
                    f, packet = self.read()
                    if f:
                        self.write(packet)
                else:
                    time.sleep(0.5)
                if current_time > self.options['end_time']:
                    logger.info('Collection is done')
                    break
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            logger.error(str(ex))

EXCHANGE = 'image_pipeline'
ROUTING_KEY_RAW = '0'
ROUTING_KEY_EXPORT = '9'

def main():
    datetime_format = '%a %b %d %H:%M:%S %Z %Y'

    parser = argparse.ArgumentParser()

    parser.add_argument('-c', dest='config_file', help='Specify config file')
    args = parser.parse_args()

    config_file = None
    if args.config_file:
        config_file = args.config_file
    else:
        config_file = '/etc/waggle/image_collector.conf'
    
    config = None
    if os.path.isfile(config_file):
        with open(config_file) as file:
            config = json.loads(file.read())
    else:
        config = {
            'start_time': time.strftime(datetime_format, time.gmttime()),
            'end_time': time.strftime(datetime_format, time.gmtime()),
            'daytime': True,
            'interval': 1,
            'verbose': False
            }
        with open(config_file, 'w') as file:
            file.write(json.dumps(config))
        logger.error('Please specify /etc/waggle/image_collector.conf file')
        exit(-1)
    
    if config['start_time'] is None or config['end_time'] is None:
        logger.error('start and end date must be provided')
        exit(-1)

    try:
        config['start_time'] = time.mktime(time.strptime(config['start_time'], datetime_format))
        config['end_time'] = time.mktime(time.strptime(config['end_time'], datetime_format))
    except Exception as ex:
        logger.error(str(ex))
        exit(-1)

    processor = ImageCollectionProcessor()
    stream = RabbitMQStreamer(logger)
    stream.config(EXCHANGE, ROUTING_KEY_RAW, ROUTING_KEY_EXPORT)
    result, message = stream.connect()
    if result:
        processor.add_handler(stream, 'in-out')
    else:
        logger.error('Cannot run RabbitMQ %s ' % (message,))
        exit(-1)
    processor.setValues(config)
    processor.run()


if __name__ == '__main__':
    main()