import base64
import glob
import json
import logging
import os
import os.path
import pika
import subprocess
import time
import cv2
import signal

import sys
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

graceful_signal_to_kill = False
datetime_format = '%a %b %d %H:%M:%S %Z %Y'

def main():
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

  script_dir = os.path.dirname(os.path.abspath(__file__))

  camera_devices = glob.glob('/dev/waggle_cam_*')
  if len(camera_devices) == 0:
    raise Exception('no available cameras detected')

  capture_config_file = '/etc/waggle/image_capture.conf'
  capture_config = None
  if os.path.isfile(capture_config_file):
    with open(capture_config_file) as config:
      capture_config = json.loads(config.read())
  else:
    capture_config = {'top':{'resolution':'1024x768', 'skip_frames':5, 'factor':90,
                             'interval':1800},
                      'bottom':{'resolution':'1920x1080', 'skip_frames':5, 'factor':90,
                                'interval':1800}}
    with open(capture_config_file, 'w') as config:
      config.write(json.dumps(capture_config))

  command = ['arp -a 10.31.81.10 | awk \'{print $4}\' | sed \'s/://g\'']
  node_id = str(subprocess.getoutput(command))

  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()

  channel.exchange_declare(exchange='image_pipeline', type='direct')

  cam_capture = {}
  for camera_device in camera_devices:
    try:
      cap = cv2.VideoCapture(camera_device)
      config = [capture_config[x] for x in capture_config if x in camera_device]
      if config is not []:
        config = config[0]
        resolution = config['resolution'].split('x')
        config['width'] = resolution[0]
        config['height'] = resolution[1]
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(config['width']))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(config['height']))
        cam_capture[camera_device] = [cap, config, time.time() - config['interval'], 0]
    except Exception as ex:
      logging.warning('Could not configure %s: %s' % (camera_device, ex))
      continue

  try:
    while not graceful_signal_to_kill:
      for device in cam_capture:
        cap, config, last_updated, failure_count = cam_capture[device]
        current_time = time.time()
        if current_time - last_updated > config['interval']:
          last_updated = current_time
          cam_capture[device] = [cap, config, last_updated, failure_count]
          f, frame = cap.read()
          if f:
            byte_frame = cv2.imencode('.jpg', frame)[1].tostring()

            logging.info("inserting {} camera image into processing pipeline...".format(device))
            packet = Packet()
            packet.meta_data = {'node_id': node_id,
                                     'image_width': config['width'],
                                     'image_height': config['height'],
                                     'device': os.path.basename(device),
                                     'producer': os.path.basename(__file__),
                                     'datetime': time.strftime(datetime_format, time.gmtime())}
            packet.raw = byte_frame
            channel.basic_publish(exchange='image_pipeline', routing_key='0', body=packet.output())
          else:
            failure_count += 1
            #TODO: frequent failure of obtaining images needs to be handled here
        time.sleep(0.1)
  except KeyboardInterrupt:
    channel.stop_consuming()
  connection.close()

  for device in cam_capture:
    cap, config, last_updated, failure_count = cam_capture[device]
    cap.release()

  # TODO:
  # 1) add RPC control of configuration
  # 2) handle SIGTERM signals

def sigterm_handler(signum, frame):
  global graceful_signal_to_kill
  graceful_signal_to_kill = True

if __name__ == '__main__':
  signal.signal(signal.SIGTERM, sigterm_handler)
  main()
