#!/usr/bin/python3

import sys
import json
import os
import logging
import time
import datetime
import binascii

# RabbitMQ Python client
import pika

# Import graphics functions
import cv2
import numpy as np

# Iport waggle processor
# TODO: Embed the python model into pywaggle library
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

# Configuration of the pipeline
# name of the pipeline
EXCHANGE = 'image_pipeline'
# output direction of this processor
ROUTING_KEY_EXPORT = 'exporter' # flush output to Beehive

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

'''
    Helper functions
'''
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
    b,g,r = cv2.split(image)

    def get_histogram_in_byte(histogram):
        mmax = np.max(histogram) / 255. # Normalize it in range of 255
        histogram = histogram / mmax
        output = bytearray()
        for value in histogram:
            output.append(int(value))
        return binascii.hexlify(output).decode()
    r_histo, bins = np.histogram(r, range(0, 256, 3))
    g_histo, bins = np.histogram(g, range(0, 256, 3))
    b_histo, bins = np.histogram(b, range(0, 256, 3))
    ret = {
        'r': get_histogram_in_byte(r_histo),
        'g': get_histogram_in_byte(g_histo),
        'b': get_histogram_in_byte(b_histo),
    }
    return ret

'''
    Collection configuration
'''
def default_configuration():
    conf = {'top': {
            'daytime': [('00:00:00', '23:59:59')], # 6 AM to 7 PM in Chicago
            'interval': 600,                       # every 60 mins
            'verbose': False
        },
        'bottom': {
            'daytime': [('00:00:00', '23:59:59')], # 6 AM to 7 PM in Chicago
            'interval': 600,                        # every 30 mins
            'verbose': False
        }
    }
    return conf

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
                except:
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
    def write(self, packet, to_stream):
        if to_stream not in self.output_handler:
            return False

        self.output_handler[to_stream].write(packet.output())
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
        @params: Packet - the packet
        @return: processed packet
    """
    def do_process(self, packet):
        nparr_img = np.fromstring(packet.raw, np.uint8)
        img = cv2.imdecode(nparr_img, cv2.IMREAD_COLOR)

        # Obtain basic information of the image
        packet.data.append({'avg_color': get_average_color(img)})
        packet.data.append({'histogram': get_histogram(img)})
        
        # Shrink image size to reduce file size
        (h, w) = img.shape[:2]
        new_width = int(2)
        r = new_width / float(w)
        new_height = int(h * r)
        dim = (new_width, new_height)
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        packet.raw = cv2.imencode('.jpg', resized)[1].tostring()

        packet.meta_data.update({
            'image_width': new_width,
            'image_height': new_height,
        })

        return packet

    """
        Main thread of the processor
    """
    def run(self):
        logger.info('Example processor has started...')
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
                                packet = self.do_process(packet)
                                self.write(packet, device)
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

if __name__ == '__main__':
    processor = ExampleProcessor()

    config = default_configuration()
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
    logger.info('Example processor terminated')