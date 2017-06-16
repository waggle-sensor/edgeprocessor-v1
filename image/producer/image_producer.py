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


  command = ['arp', '-a', '10.31.81.10', '|', 'awk', '{print $4}', '|', 'sed', 's/://g']
  node_id = str(subprocess.check_output(command))

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
        config['width'] = float(resolution[0])
        config['height'] = float(resolution[1])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['width'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['height'])
    except Exception as ex:
      logging.warning('Could not configure %s: %s' % (camera_device, ex))
      continue
    cam_capture[camera_device] = [cap, config, time.time()]

  try:
    while True:
      for device in cam_capture:
        cap, config, last_updated = cam_capture[device]
        current_time = time.time()
        if current_time - last_updated > config['interval']:
          last_updated = current_time
          cam_capture[device] = [cap, config, last_updated]
          f, frame = cap.read()
          if f:
            byte_frame = cv2.imencode('.jpg', frame)[1].tostring()
            base64_frame = base64.b64encode(byte_frame).decode()

            logging.info("inserting {} camera image into processing pipeline...".format(cam_location))
            message = {'meta_data': {'node_id': node_id,
                                     'image_width': config['width'],
                                     'image_height': config['height'],
                                     'device': device,
                                     'producer': path.basename(__file__),
                                     'datetime': time.time()},
                       'results': [],
                       'image': base64_frame}
            channel.basic_publish(exchange='image_pipeline', routing_key='0', body=json.dumps(message))
  except KeyboardInterrupt:
    channel.stop_consuming()
  connection.close()

  # TODO:
  # 1) add RPC control of configuration
  # 2) handle SIGTERM signals

if __name__ == '__main__':
  main()
