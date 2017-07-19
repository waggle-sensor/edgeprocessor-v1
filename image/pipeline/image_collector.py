import pika
import json
import cv2
import numpy as np
import time
import argparser
import sys
import logging
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

EXCHANGE = 'image_pipeline'
ROUTING_KEY_RAW = '0'
ROUTING_KEY_EXPORT = '9'





def collection(start_time, end_time, interval, daytime=True, verbose=False):

    def on_process(ch, method, props, body):
        try:
            print(start_time)
            # Export the image
            ch.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY_EXPORT, body=body)
        except Exception as ex:
            logging.error(ex)

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


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser()

    parser.add_argument('--st', dest='start_datetime', help='Start collection datetime in UTC')
    parser.add_argument('--et', dest='end_datetime', help='End collection datetime in UTC')

    parser.add_argument('--daytime', dest='daytime', help='Collect only in daytime', action='store_true')
    parser.add_argument('--interval', dest='interval', help='Interval of collection in seconds')

    parser.add_argument('-v', dest='verbose', help='Verbose', action='store_true')
    args = parser.parse_args()

    if args.start_datetime.empty() or args.end_datetime.empty() or args.interval.empty():
        logging.error('Arguments must be provided')
        parser.print_help()
        exit(-1)

    start = end = None
    try:
        datetime_format = '%a %b %d %H:%M:%S %Z %Y'
        start = time.strptime(args.start_datetime, datetime_format)
        end = time.strptime(args.end_datetime, datetime_format)
    except Exception as ex:
        logging.error(str(ex))
        exit(-1)

    collection(start, end, args.interval, args.daytime, args.verbose)


if __name__ == '__main__':
    main()