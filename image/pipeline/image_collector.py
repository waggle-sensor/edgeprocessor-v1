#!/usr/bin/env python3

import os
import pika
import json
import cv2
import numpy as np
import time
import datetime
import argparse
import sys
import logging
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

datetime_format = '%a %b %d %H:%M:%S %Z %Y'

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

def default_configuration():
    conf = {
        'start_time': time.time(),
        'end_time': time.time(),
        'daytime': ('00:00:00', '23:59:59'),
        'target': 'bottom',
        'interval': 1,
        'verbose': False
    }
    return conf


class ImageCollectionProcessor(Processor):
    def __init__(self):
        super().__init__()
        self.options = default_configuration()

    def setValues(self, options):
        self.options.update(options)

    def close(self):
        for in_handler in self.input_handler:
            in_handler.close()
        for out_handler in self.output_handler:
            out_handler.close()

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

    def check_daytime(self, current_time, daytime_start, duration):
        time_now = datetime.datetime.fromtimestamp(current_time)
        daytime_start = time_now.replace(hour=daytime_start[0], minute=daytime_start[1], second=daytime_start[2])

        diff_in_second = (time_now - daytime_start).total_seconds()
        if diff_in_second < 0:
            return False, abs(diff_in_second)
        elif diff_in_second > duration:
            return False, 3600 * 24 - diff_in_second # wait until midnight
        return True, 0

    def run(self):
        while time.time() <= self.options['start_time']:
            time.sleep(self.options['start_time'] - time.time())

        daytime_duration = 3600 * 24 # covers one full day; collect all day long
        daytime_start = [0, 0, 0] # Default
        try:
            daytime_start = [int(x) for x in self.options['daytime'][0].split(':')]
            daytime_end = [int(x) for x in self.options['daytime'][1].split(':')]
            daytime_duration = (daytime_end[0] - daytime_start[0]) * 3600 + (daytime_end[1] - daytime_start[1]) * 60 + (daytime_end[2] - daytime_start[2])
        except Exception as ex:
            logger.error(str(ex))

        logger.info('Collection started')
        try:
            last_updated_time = time.time()
            while True:
                current_time = time.time()
                if current_time - last_updated_time > self.options['interval']:
                    # Check if now is in the daytime
                    result, wait_time = self.check_daytime(current_time, daytime_start, daytime_duration)
                    if result:
                        f, packet = self.read()
                        if f:
                            # Check if the image is the target
                            if 'device' in packet.meta_data:
                                device = packet.meta_data['device']
                                if self.options['target'] in device:
                                    self.write(packet)
                                    last_updated_time = current_time
                        else:
                            time.sleep(self.options['interval'])
                    else:
                        time.sleep(wait_time)
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
        try:
            with open(config_file) as file:
                config = json.loads(file.read())
        except Exception as ex:
            logger.error('Cannot load configuration: %s' % (str(ex),))
            exit(-1)
    else:
        config = default_configuration()
        with open(config_file, 'w') as file:
            file.write(json.dumps(config))
        logger.info('No config specified; default will be used. For detail, check /etc/waggle/image_collector.conf')
    
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

    processor.close()
    logger.info('Collector terminated')

if __name__ == '__main__':
    main()
