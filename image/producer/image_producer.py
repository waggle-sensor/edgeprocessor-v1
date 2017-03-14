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
  #output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]

  # 1) determine available video devices (/dev/waggle_cam_top and /dev/waggle_cam_bottom for now)
  camera_devices = glob.glob('/dev/waggle_cam_*')

  # 2) read image capture configuration from /etc/waggle/image_capture.conf, or
  #    create a default configuration if non-existent
  capture_config_file = '/etc/waggle/image_capture.conf'
  capture_config = None
  if os.path.isfile(capture_config_file):
    with open(capture_config_file) as config:
      capture_config = json.loads(config.read())
  else:
    capture_config = {'top':{'resolution':'3264x2440', 'skip_frames':20, 'interval':60}}
    with open(capture_config_file, 'w') as config:
      config.write(json.dumps(capture_config))

  # 3) create "image_pipeline" fanout exchange
  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()
  channel.exchange_declare(exchange='image_pipeline', type='fanout')

  # 4) loop until killed
  while True:
    # 5) for each camera
    for camera_device in camera_devices:
      # 5a)   grab camera image
      command = ['/usr/bin/fswebcam', '-d', camera_device, '-S', str(capture_config['skip_frames']),
                 '-r', capture_config['resolution'], '--jpeg', '-q', '-D', '0']
      image = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]

      # 5b)   annotate and send image to exchange
      timestamp = str(int(time.time()))
      message = {'results':[timestamp,], 'image':base64.b64encode(image) }
      channel.basic_publish(exchange='image_pipeline', routing_key='', body=json.dumps(message))
    # 6) sleep for configured capture interval
    time.sleep(capture_config['interval'])
  
  # TODO:
  # 1) add RPC control of configuration
  # 2) handle SIGTERM and keyboard signals nicely

if __name__ == '__main__':
  main()
