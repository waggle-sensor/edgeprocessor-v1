#!/usr/bin/python3

import sys
import os
import time
import datetime
import binascii
from queue import Queue
from threading import Thread, Event
from collections import deque

import pika

# Import graphics functions
import cv2
import numpy as np

# Import waggle processor
# TODO: Embed the python model into pywaggle library
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import Processor

# Configuration of the pipeline
# name of the pipeline
EXCHANGE = 'image_pipeline'

# output direction of this processor
ROUTING_KEY_EXPORT = 'exporter'  # flush output to Beehive


def get_average_color(image):
    avg_color = np.average(image, axis=0)
    avg_color = np.average(avg_color, axis=0)

    ret = {
        'r': int(avg_color[2]),
        'g': int(avg_color[1]),
        'b': int(avg_color[0]),
    }
    return ret


def get_histogram(image):
    b, g, r = cv2.split(image)

    def get_histogram_in_byte(histogram):
        mmax = np.max(histogram) / 255.  # Normalize it in range of 255
        histogram = histogram / mmax
        output = bytearray()
        for value in histogram:
            output.append(int(value))
        return binascii.hexlify(output).decode()
    r_histo, bins = np.histogram(r, range(0, 256))
    g_histo, bins = np.histogram(g, range(0, 256))
    b_histo, bins = np.histogram(b, range(0, 256))
    ret = {
        'r': get_histogram_in_byte(r_histo),
        'g': get_histogram_in_byte(g_histo),
        'b': get_histogram_in_byte(b_histo),
    }
    return ret


def default_configuration():
    conf = {
        'top': {
            'daytime': [('00:00:00', '23:59:59')],  # All day long
            'interval': 60,                        # every 5 mins
            'verbose': True
        },
        'bottom': {
            'daytime': [('00:00:00', '23:59:59')],  # All day long
            'interval': 60,                        # every 5 mins
            'verbose': True
        }
    }
    return conf


class PipelineWriter(object):
    def __init__(self, routing_out, exchange='image_pipeline'):
        self.connection = None
        self.channel = None
        self.out_key = routing_out
        self.exchange = exchange

    def open(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
        return True

    def close(self):
        if self.connection is not None:
            if self.connection.is_open:
                self.connection.close()
            self.connection = None
            self.channel = None

    def write(self, frame, headers):
        properties = pika.BasicProperties(
            headers=headers,
            delivery_mode=2,
            timestamp=int(time.time() * 1000),
            content_type='b')
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.out_key,
            properties=properties,
            body=frame)


class PipelineReader(Thread):
    def __init__(self, routing_in, exchange='image_pipeline'):
        Thread.__init__(self)
        self.is_available = Event()
        self.last_message = deque(maxlen=1)
        self.connection = None
        self.channel = None
        self.exchange = exchange
        self.routing_in = routing_in

    def open(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct')

        result = self.channel.queue_declare(exclusive=True, arguments={'x-max-length': 1})
        self.queue = result.method.queue
        self.channel.queue_bind(queue=self.queue, exchange=self.exchange, routing_key=self.routing_in)
        self.start()
        return True

    def close(self):
        if self.connection is not None:
            if self.connection.is_open:
                self.channel.stop_consuming()
                self.channel.close()
                self.connection.close()
                self.join()

    def read(self):
        try:
            return True, self.last_message.pop()
        except IndexError:
            return False, ''

    def _rmq_callback(self, channel, method, properties, body):
        self.last_message.append((properties.headers, body))
        self.is_available.set()

    def run(self):
        try:
            self.channel.basic_consume(self._rmq_callback, queue=self.queue, no_ack=True)
            self.channel.start_consuming()
        except Exception:
            pass
        print('done)')


class ExampleProcessor(Processor):
    def __init__(self):
        super().__init__()

    """
        Load configuration
        @params: Dict - configuration
    """
    def set_configs(self, configs):
        for device in configs:
            device_option = configs[device]
            durations = []
            for start, end in device_option['daytime']:
                try:
                    start_sp = start.split(':')
                    end_sp = end.split(':')
                    durations.append(((int(start_sp[0]), int(start_sp[1]), int(start_sp[2])), (int(end_sp[0]), int(end_sp[1]), int(end_sp[2]))))
                except Exception:
                    durations = [((0, 0, 0), (23, 59, 59))]
                    break
            device_option['daytime'] = durations
            configs[device] = device_option
        self.config = configs

        # The processor will receive frames as soon as it runs
        for device in self.config:
            device_option = self.config[device]
            device_option['last_updated_time'] = time.time() - device_option['interval'] - 1

    """
        Close input/output handlers
    """
    def close(self):
        for in_handler in self.input_handler:
            self.input_handler[in_handler].close()
        for out_handler in self.output_handler:
            self.output_handler[out_handler].close()

    """
        Read frames from input handlers
        This is non-blocking call
        @params: String - name of the input stream
        @return: result of operation, a frame from the target stream
    """
    def read(self, from_stream):
        if from_stream not in self.input_handler:
            return False, None

        return self.input_handler[from_stream].read()

    """
        Write data into output handlers
        @params: Packet - processed packet
                 String - name of the output stream
        @return: result of operation
    """
    def write(self, frame, headers, to_stream):
        if to_stream not in self.output_handler:
            return False

        self.output_handler[to_stream].write(frame, headers)
        return True

    """
        Check if current time is bounded within daytime
        @params: Time - current time in time epoch
                 List - durations of the daytime
        @return: result of operation, the time to wait for incoming daytime in seconds
    """
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

    """
        Main function of the processor
        @params: frame: binary blob
                 headers: Dictionary

        @return: (processed frame, processed headers)
    """
    def do_process(self, frame, headers):
        results = {}
        nparr_img = np.fromstring(frame, np.uint8)
        img = cv2.imdecode(nparr_img, cv2.IMREAD_COLOR)

        # Obtain basic information of the image
        results['avg_color'] = get_average_color(img)
        results['histogram'] = get_histogram(img)

        prev_results = []
        if 'results' in headers:
            prev_results = headers['results']
        prev_results.append({os.path.basename(__file__): results})
        headers['results'] = prev_results

        # Shrink image size to reduce file size
        (h, w) = img.shape[:2]
        new_width = int(2)
        r = new_width / float(w)
        new_height = int(h * r)
        dim = (new_width, new_height)
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        frame = cv2.imencode('.jpg', resized)[1].tostring()

        headers.update({
            'image_width': new_width,
            'image_height': new_height,
        })

        return headers, frame

    """
        Main thread of the processor
    """
    def run(self):
        print('Example processor has started...')
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
                                headers, frame = packet
                                headers.update({'processing_software': os.path.basename(__file__)})
                                headers, frame = self.do_process(frame, headers)

                                self.write(frame, headers, ROUTING_KEY_EXPORT)
                                device_option['last_updated_time'] = current_time
                                if device_option['verbose']:
                                    print('An image from %s has been published' % (device,))
                        else:
                            device_option['last_updated_time'] = current_time + min(wait_time, device_option['interval'])
                    self.config[device] = device_option

                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as ex:
                print(str(ex))
                break


if __name__ == '__main__':
    processor = ExampleProcessor()

    config = default_configuration()
    for device in config:
        try:
            stream_in = PipelineReader(device, EXCHANGE)
            result = stream_in.open()
            if result:
                processor.add_handler(stream_in, handler_name=device, handler_type='in')
            else:
                stream_in.close()
                raise Exception('Unable to set streaming input for %s' % (device))
            stream_out = PipelineWriter(ROUTING_KEY_EXPORT, EXCHANGE)
            result = stream_out.open()
            if result:
                processor.add_handler(stream_out, handler_name=ROUTING_KEY_EXPORT, handler_type='out')
            else:
                stream_out.close()
                raise Exception('Unable to set streaming output for %s' % (device))
        except Exception as ex:
            print(str(ex))

    processor.set_configs(config)
    processor.run()
    processor.close()
    print('Example processor terminated')
