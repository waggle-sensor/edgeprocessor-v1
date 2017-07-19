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

EXCHANGE = 'image_pipeline'
ROUTING_KEY_RAW = '0'
ROUTING_KEY_EXPORT = '9'

datetime_format = '%a %b %d %H:%M:%S %Z %Y'

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

start_time = end_time = interval = daytime = None

def on_process(ch, method, props, body):
    global start_time, end_time, interval, daytime
    try:
        print(start_time)
        # Export the image
        ch.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY_EXPORT, body=body)
    except Exception as ex:
        logging.error(ex)


def collection(start_time, end_time, interval=1, daytime=True, verbose=False):
    global start_time, end_time, interval, daytime
    st 
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        result = channel.queue_declare(exclusive=True)
        my_queue = result.method.queue
        channel.queue_bind(queue=my_queue, exchange=EXCHANGE, routing_key=ROUTING_KEY_RAW)

        channel.basic_consume(on_process, queue=my_queue, no_ack=True)
        channel.start_consuming()
    except Exception as ex:
        logging.error(str(ex))
        channel.stop_consuming()


class ImageCollectionProcessor(Processor):
    def __init__(self):
        super().__init__()
        self.options = {
        'start_time': time.time(),
        'end_time': time.time(),
        'daytime': True
        'interval': 1
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
            'start_date': time.strftime(datetime_format, time.gmttime()),
            'end_date': time.strftime(datetime_format, time.gmttime()),
            'daytime': True,
            'interval': 1,
            'verbose': False
            }
        with open(config_file, 'w') as file:
            file.write(json.dumps(config))
        logger.info('Please specify /etc/waggle/image_collector.conf file')
        exit(-1)
    
    if config['start_date'] is None or config['end_date'] is None:
        logger.error('start and end date must be provided')
        exit(-1)

    try:
        config['start_date'] = time.mktime(time.strptime(config['start_date'], datetime_format))
        config['end_date'] = time.mktime(time.strptime(config['end_date'], datetime_format))
    except Exception as ex:
        logger.error(str(ex))
        exit(-1)

    processor = ImageCollectionProcessor()
    processor.setValues(config)


if __name__ == '__main__':
    main()