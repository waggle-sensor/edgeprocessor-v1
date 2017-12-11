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
    conf = {'top': {
            'daytime': [('12:00:00', '23:00:00')], # 6 AM to 7 PM in Chicago
            'interval': 3600,                       # every 60 mins
            'verbose': False
        },
        'bottom': {
            'daytime': [('12:00:00', '23:00:00')], # 6 AM to 7 PM in Chicago
            'interval': 900,                        # every 15 mins
            'verbose': False
        }
    }
    return conf


class ImageCollectionProcessor(Processor):
    def __init__(self):
        super().__init__()

    def set_configs(self, configs):
        for device in configs:
            device_option = configs[device]
            durations = []
            for start, end in device_option['daytime']:
                try:
                    start_sp = start.split(':')
                    end_sp = end.split(':')
                    durations.append(((int(start_sp[0]), int(start_sp[1]), int(start_sp[2])), (int(end_sp[0]), int(end_sp[1]), int(end_sp[2]))))
                except:
                    durations = [((0, 0, 0), (23, 59, 59))]
                    break
            device_option['daytime'] = durations
            configs[device] = device_option
        self.config = configs

    def close(self):
        for in_handler in self.input_handler:
            self.input_handler[in_handler].close()
        for out_handler in self.output_handler:
            self.output_handler[out_handler].close()

    def read(self, from_stream):
        if from_stream not in self.input_handler:
            return False, None

        return self.input_handler[from_stream].read()
        
    def write(self, packet, to_stream):
        if to_stream not in self.output_handler:
            return False

        self.output_handler[to_stream].write(packet.output())
        return True

    def check_daytime(self, current_time, durations):
        time_now = datetime.datetime.fromtimestamp(current_time)
        time_start = time_end = None
        for start, end in durations:
            start_hours, start_minutes, start_seconds = start
            end_hours, end_minutes, end_seconds = end
            time_start = time_now.replace(hour=start_hours, minute=start_minutes, second=start_seconds)
            time_end = time_now.replace(hour=end_hours, minute=end_minutes, second=end_seconds)
            if time_start <= time_now <= time_end:
                return True, 0
            elif time_start > time_now:
                return False, int((time_start - time_now).total_seconds())
        end_of_today = time_now.replace(hour=23, minute=59, second=59)
        return False, int((end_of_today - time_now).total_seconds())

    def run(self):
        for device in self.config:
            device_option = self.config[device]
            device_option['last_updated_time'] = time.time() - device_option['interval'] - 1

        logger.info('Collection started')
        while True:
            try:
                current_time = time.time()

                for device in self.config:
                    device_option = self.config[device]

                    if current_time - device_option['last_updated_time'] > device_option['interval']:
                        result, wait_time = self.check_daytime(current_time, device_option['daytime'])

                        if result:
                            f, packet = self.read(device)
                            if f:
                                packet.meta_data.update({'processing_software': os.path.basename(__file__)})
                                self.write(packet)
                                device_option['last_updated_time'] = current_time
                                if device_option['verbose']:
                                    logger.info('An image from %s has been published' % (device,))
                        else:
                            device_option['last_updated_time'] = current_time + min(wait_time, device_option['interval'])
                    self.config[device] = device_option

                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as ex:
                logger.error(str(ex))
                break

EXCHANGE = 'image_pipeline'
ROUTING_KEY_EXPORT = 'exporter'

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', dest='config_file', help='Specify config file')
    args = parser.parse_args()

    config_file = None
    if args.config_file:
        config_file = args.config_file
    else:
        config_file = '/wagglerw/waggle/image_collector.conf'
    
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
        logger.info('No config specified; default will be used. For detail, check %s' % (config_file,))

    processor = ImageCollectionProcessor()

    for device in config:
        try:
            stream = RabbitMQStreamer(logger)
            stream.config(EXCHANGE, device, ROUTING_KEY_EXPORT)
            result, message = stream.connect()
            if result:
                processor.add_handler(stream, handler_name=device, handler_type='in-out')
            else:
                logger.error('Unable to set streamer for %s:%s ' % (device, message))
                stream.close()
        except Exception as ex:
            logger.error(str(ex))

    processor.set_configs(config)
    processor.run()

    processor.close()
    logger.info('Collector terminated')

if __name__ == '__main__':
    main()
