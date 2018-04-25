#! /usr/bin/python3

import os
import subprocess
import time
import fcntl
import mmap
import select
from threading import Thread, Event
from queue import Queue

import v4l2
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
        'timestamp': str(timestamp)
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


class Camera(object):
    def __init__(self, device):
        if os.path.exists(device):
            self.device = device
        else:
            raise Exception('Device not available')

    def __repr__(self):
        return self.device

    def __enter__(self):
        print('ha')
        self.fd = open(self.device, 'rb+', buffering=0)
        return self

    def __exit__(self, type, value, traceback):
        print('ah')
        self._stop()
        self.fd.close()

    def _create_buffer(self, buffer_size=30):
        req = v4l2.v4l2_requestbuffers()
        req.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        req.memory = v4l2.V4L2_MEMORY_MMAP
        req.count = buffer_size  # nr of buffer frames
        fcntl.ioctl(self.fd, v4l2.VIDIOC_REQBUFS, req)  # tell the driver that we want some buffers

        self.buffers = []
        for ind in range(req.count):
            # setup a buffer
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
            buf.memory = v4l2.V4L2_MEMORY_MMAP
            buf.index = ind
            fcntl.ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            mm = mmap.mmap(
                self.fd.fileno(),
                buf.length,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=buf.m.offset
            )
            self.buffers.append(mm)

            # queue the buffer for capture
            fcntl.ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)

    def print_capability(self):
        cp = v4l2.v4l2_capability()
        fcntl.ioctl(self.fd, v4l2.VIDIOC_QUERYCAP, cp)
        print(cp.driver)
        print("Draiver:", "".join((chr(c) for c in cp.driver)))
        print("Name:", "".join((chr(c) for c in cp.card)))
        print("Is a video capture device?", bool(cp.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE))
        print("Supports read() call?", bool(cp.capabilities & v4l2.V4L2_CAP_READWRITE))
        print("Supports streaming?", bool(cp.capabilities & v4l2.V4L2_CAP_STREAMING))

    def _set_resolution(self, width, height, pixelformat='MJPG'):
        fmt = v4l2.v4l2_format()
        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        fcntl.ioctl(self.fd, v4l2.VIDIOC_G_FMT, fmt)  # get current settings
        fmt.fmt.pix.width = width
        fmt.fmt.pix.height = height
        fourcc = (ord(pixelformat[0])) | (ord(pixelformat[1]) << 8) | (ord(pixelformat[2]) << 16) | (ord(pixelformat[3]) << 24)
        fmt.fmt.pix.pixelformat = fourcc
        fcntl.ioctl(self.fd, v4l2.VIDIOC_S_FMT, fmt)

    def _start(self):
        self.buf_type = v4l2.v4l2_buf_type(v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE)
        fcntl.ioctl(self.fd, v4l2.VIDIOC_STREAMON, self.buf_type)

    def _stop(self):
        if hasattr(self, 'buf_type'):
            fcntl.ioctl(self.fd, v4l2.VIDIOC_STREAMOFF, self.buf_type)

    def configure_and_go(self, width, height, buffer_size=30):
        self._set_resolution(width, height)
        self._create_buffer(buffer_size)
        self._start()

    def capture(self):
        select.select([self.fd], [], [])
        buf = v4l2.v4l2_buffer()
        buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        buf.memory = v4l2.V4L2_MEMORY_MMAP
        fcntl.ioctl(self.fd, v4l2.VIDIOC_DQBUF, buf)  # get image from the driver queue

        mm = self.buffers[buf.index]
        result = mm.read(buf.bytesused)
        mm.seek(0)
        fcntl.ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)  # requeue the buffer
        return result


class CaptureWorker(Thread):
    def __init__(self, event, device, width, height):
        Thread.__init__(self)
        self.device = device
        self.event = event
        self.out = Queue(1)
        self.width = width
        self.height = height
        self.is_closed = False

    def close(self):
        self.is_closed = True

    def get(self):
        if self.out.empty():
            return False, None
        return True, self.out.get()

    def run(self):
        try:
            with Camera(self.device) as camera:
                camera.configure_and_go(self.width, self.height)
                while not self.is_closed:
                    raw_frame = camera.capture()
                    if len(raw_frame) > 0:
                        if self.out.empty():
                            self.out.put(raw_frame)
                            self.event.set()
        except KeyboardInterrupt:
            print('Interrupted')
        except Exception as ex:
            print(str(ex))
        finally:
            self.is_closed = True


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

                    cam_capture[camera_device] = [cap, e, config]
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
    # print('image producer is currently under construction...Looping infinitely...')
    # try:
    #     while True:
    #         time.sleep(1)
    # except (KeyboardInterrupt, Exception) as ex:
    #     pass
    main()
