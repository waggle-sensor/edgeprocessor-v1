import json
import logging
import os
import os.path
import pika
import time
import io

null_exif = {
  '0th': {},
  'Exif': {},
  'GPS': {},
  'Interop': {},
  '1st': {},
  'thumbnail': None
}


def generate_meta_data(meta_data, results):
  meta_data = null_exif.copy()
  oth = meta_data['0th']
  if 'image_width' in meta_data:
    oth[piexif.ImageIFD.ImageWidth] = meta_data['image_width']
  if 'image_height' in meta_data:
    oth[piexif.ImageIFD.ImageLength] = meta_data['image_height']
  if 'node_id' in meta_data:
    oth[piexif.ImageIFD.Make] = meta_data['node_id']
  if 'device' in meta_data:
    oth[piexif.ImageIFD.Artist] = meta_data['device']
  if 'producer' in meta_data:
    oth[piexif.ImageIFD.Software] = producer_name
  if 'datetime' in meta_data:
    oth[piexif.ImageIFD.DateTime] = time.strftime('%Y:%m:%d %H:%M:%S', time.gmttime(meta_data['datetime']))  # last time the image changed
  meta_data['0th'] = oth

  exif = meta_data['Exif']
  if results is not []:
    exif[piexif.ExifIFD.UserComment] = json.dumps({'results': results})
  # exif[piexif.ExifIFD.DateTimeOriginal] = time.strftime('%Y:%m:%d %H:%M:%S',
  #                                                       time.gmttime())  # YYYY:MM:DD HH:MM:SS date time
  meta_data['Exif'] = exif
  return meta_data


def make_image_bytes(meta_data, additional_info, image):
  ret = io.BytesIO()

  # # make sure all exif keys are integer
  # for entity in meta_data:
  #   if isinstance(meta_data[entity], dict):
  #     meta_data[entity] = {int(key): value for key, value in meta_data[entity].items() if key.isdigit()}

  exif = generate_meta_data(meta_data, additional_info)
  exif_bytes = piexif.dump(exif)
  piexif.insert(exif_bytes, image, ret)
  return ret


def process_image(channel, method, properties, body):
  logging.info(" [x] pushing image to export queue...")
  message = json.loads(body.decode())

  # if the message contains image
  if 'image' in message:
    image_byte = make_image_bytes(message['meta_data'], message['results'], base64.b64decode(message['image']))
    channel.basic_publish(exchange='', routing_key='images', body=image_byte.read(), properties=properties)
  else:
    # send message['results'] to data queue
    # TODO: data queue in edge processor does not exist, a shovel corresponding to the data queue is needed
    channel.basic_publish(exchange='', routing_key='images', body=body, properties=properties)


def main():
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

  script_dir = os.path.dirname(os.path.abspath(__file__))

  export_stage_path = '/etc/waggle/export_stage'
  if os.path.isfile(export_stage_path):
    with open(export_stage_path) as export_stage_file:
      export_stage = export_stage_file.read()
  else:
    export_stage = '9'

  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()
  channel.exchange_declare(exchange='image_pipeline', type='direct')
  queue = channel.queue_declare(exclusive=True)

  # Binding consistently fails on a clean RMQ broker unless
  # a small delay is introduced between declarations and binding
  time.sleep(1)

  channel.queue_bind(exchange='image_pipeline', queue=queue.method.queue,
                     routing_key=export_stage)
  channel.queue_declare(queue='images', arguments={"x-max-length":32})

  channel.basic_consume(process_image, queue=queue.method.queue, no_ack=True)
  try:
    channel.start_consuming()
  except KeyboardInterrupt:
    channel.stop_consuming()
  connection.close()

if __name__ == '__main__':
  main()
