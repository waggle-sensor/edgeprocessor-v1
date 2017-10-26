import json
import logging
import os
import os.path
import pika
import time

def process_image(channel, method, properties, body):
  logging.info(" [x] pushing image to export queue...")
  channel.basic_publish(exchange='', routing_key='images', body=body, properties=properties)


def main():
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

  script_dir = os.path.dirname(os.path.abspath(__file__))

  export_stage_path = '/etc/waggle/export_stage'
  if os.path.isfile(export_stage_path):
    with open(export_stage_path) as export_stage_file:
      export_stage = export_stage_file.read()
  else:
    export_stage = '0'

  connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
  channel = connection.channel()
  channel.exchange_declare(exchange='image_pipeline', exchange_type='direct')
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
