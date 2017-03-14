import base64
import glob
import json
import os
import os.path
import pika
import subprocess
import time

def main():
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
    capture_config = {'top':{'resolution':'3264x2440', 'skip_frames':20, 'interval':60},
                      'bottom':{'resolution':'3264x2440', 'skip_frames':20, 'interval':60}}
    with open(capture_config_file, 'w') as config:
      config.write(json.dumps(capture_config))

  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()
  channel.exchange_declare(exchange='image_pipeline', type='headers')

  properties = pika.BasicProperties(headers = {'stage':0})

  while True:
    for camera_device in camera_devices:
      config = {}
      if 'top' in camera_device:
        config = capture_config['top']
      else:
        config = capture_config['bottom']

      command = ['/usr/bin/fswebcam', '-d', camera_device, '-S', str(config['skip_frames']),
                 '-r', config['resolution'], '--no-banner', '--jpeg', '-1', '-D', '0', '-q', '-']
      image = str(base64.b64encode(subprocess.check_output(command)))

      timestamp = str(int(time.time()))
      message = {'results':[timestamp,], 'image':image }
      channel.basic_publish(exchange='image_pipeline', routing_key='', body=json.dumps(message),
                            properties=properties)
    time.sleep(config['interval'])
  
  # TODO:
  # 1) add RPC control of configuration
  # 2) handle SIGTERM and keyboard signals nicely

if __name__ == '__main__':
  main()
