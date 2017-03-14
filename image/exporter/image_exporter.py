import json
import os
import os.path
import pika
import time

class ImageProcessor():
  def __init__(self):
    pass
  def process_image(self, channel, method, properties, body):
    pass

class ImageExporter(ImageProcessor):
  def __init__(self, export_stage):
    super().__init__()
    self.export_stage = export_stage

  def process_image(channel, method, properties, body):
    """check each image message"""
    message = json.loads(body)
    if len(message['results']) == self.export_stage:
      channel.basic_publish(exchange='', routing_key='images', body=body)

def process_image(channel, method, properties, body):
  channel.basic_publish(exchange='', routing_key='images', body=body, properties=properties)


def main():
  script_dir = os.path.dirname(os.path.abspath(__file__))

  export_stage_path = '/etc/waggle/export_stage'
  if os.path.isfile(export_stage_path):
    with open(export_stage_path) as export_stage_file:
      export_stage = int(export_stage_file.read())
  else:
    export_stage = 1

  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()
  channel.exchange_declare(exchange='image_pipeline', type='headers')
  queue = channel.queue_declare(exclusive=True)
  channel.queue_bind(exchange='image_pipeline', queue=queue.method.queue, routing_key='',
                     arguments = {'stage':export_stage, 'x-match':'any'})
  channel.queue_declare(queue='images')

  exporter = ImageExporter(export_stage)
  channel.basic_consume(process_image, queue=queue.method.queue, no_ack=True)
  try:
    channel.start_consuming()
  except KeyboardInterrupt:
    channel.stop_consuming()
  connection.close()

if __name__ == '__main__':
  main()
