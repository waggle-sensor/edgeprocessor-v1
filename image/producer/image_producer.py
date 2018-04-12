#! /usr/bin/python3

import os
import subprocess
import time
import select
from threading import Thread, Event
from queue import Queue

import v4l2capture
import pika
import signal
import glob
import json

graceful_signal_to_kill = False
producer_name = os.path.basename(__file__)


def get_default_configuration():
    default_configuration = {
        'top': {
            'resolution': '3264x2448',
            'rotate': 0,
        },
        'bottom': {
            'resolution': '2592x1944',
            'rotate': 180,
        }
    }
    return default_configuration


def get_rmq_connection():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='image_pipeline', exchange_type='direct')
        return channel
    except Exception:
        return None


def send_to_rmq(channel, frame, timestamp, config):
    headers = {
        'node_id': config['node_id'],
        'image_width': config['width'],
        'image_height': config['height'],
        'image_format': 'MJPG',
        'image_size': len(frame),
        'image_rotate': config['rotate'],
        'device': config['device'],
        'producer': producer_name,
        'timestamp': timestamp
    }
    properties = pika.BasicProperties(
        headers=headers,
        delivery_mode=2,
        timestamp=int(timestamp * 1000),
        content_type='b')
    channel.basic_publish(
        exchange='image_pipeline',
        routing_key=config['device'],
        properties=properties,
        body=frame)


class Camera(Thread):
    def __init__(self, event, device, width, height):
        Thread.__init__(self)
        self.cap = v4l2capture.Video_device(device)
        self.event = event
        self.out = Queue(1)
        self.width = width
        self.height = height
        self.is_closed = False

    def open(self):
        ret_x, ret_y = self.cap.set_format(self.width, self.height, fourcc='MJPG')
        if self.width != ret_x or self.height != ret_y:
            self.close()
            return False
        self.cap.create_buffers(30)
        self.cap.queue_all_buffers()
        return True

    def close(self):
        self.is_closed = True

    def get(self):
        if self.out.empty():
            return False, None
        return True, self.out.get()

    def run(self):
        try:
            self.cap.start()
            while not self.is_closed:
                select.select((self.cap,), (), (),)  # 1 second timeout
                raw_frame = self.cap.read_and_queue()
                if len(raw_frame) > 0:
                    if self.out.empty():
                        self.out.put(raw_frame)
                        self.event.set()
        except Exception as ex:
            print(str(ex))
        finally:
            self.is_closed = True
            self.cap.close()


def main():
    global graceful_signal_to_kill
    camera_devices = glob.glob('/dev/waggle_cam_*')
    if len(camera_devices) == 0:
        print('No available cameras detected!')
        exit(1)

    # Load configuration
    capture_config_file = '/wagglerw/waggle/image_capture.conf'
    capture_config = None
    try:
        with open(capture_config_file) as config:
            capture_config = json.loads(config.read())
    except Exception:
        capture_config = get_default_configuration()
        with open(capture_config_file, 'w') as config:
            config.write(json.dumps(capture_config, sort_keys=True, indent=4))

    # Get node_id for maker field of the images
    command = ['arp -a 10.31.81.10 | awk \'{print $4}\' | sed \'s/://g\'']
    node_id = str(subprocess.getoutput(command))

    rmq_channel = get_rmq_connection()
    if rmq_channel is None:
        print('Could not connect to RabbitMQ!')
        exit(1)

    cam_capture = {}
    for camera_device in camera_devices:
        try:
            config = []
            for camera_name in capture_config:
                if camera_name in camera_device:
                    config = capture_config[camera_name]
                    config.update({'device': camera_name})
                    config['node_id'] = node_id

                    resolution = config['resolution'].split('x')
                    config['width'] = int(resolution[0])
                    config['height'] = int(resolution[1])
                    e = Event()
                    cap = Camera(
                        event=e,
                        device=camera_device,
                        width=config['width'],
                        height=config['height']
                    )

                    if cap.open():
                        cam_capture[camera_device] = [cap, e, config]
                    else:
                        raise Exception('Could not set the resolution')
        except Exception as ex:
            print('Could not configure %s: %s' % (camera_device, ex))

    for device in cam_capture:
        cap, event, config = cam_capture[device]
        print('%s is starting...' % (device,))
        cap.start()
        time.sleep(1)

    try:
        while not graceful_signal_to_kill:
            for device in cam_capture:
                cap, event, config = cam_capture[device]
                if cap.is_closed:
                    raise Exception('%s is closed. Restarting...' % (device,))
                else:
                    event.wait(0.01)
                    f, frame_raw = cap.get()
                    if f:
                        send_to_rmq(rmq_channel, frame_raw, time.time(), config)
                    event.clear()
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        print(str(ex))
    finally:
        graceful_signal_to_kill = False
        for device in cam_capture:
            cap, event, config = cam_capture[device]
            cap.close()
            cap.join()


# TODO:
# 1) add RPC control of configuration
# 2) handle SIGTERM signals
def sigterm_handler(signum, frame):
    global graceful_signal_to_kill
    graceful_signal_to_kill = True


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, sigterm_handler)
    main()
