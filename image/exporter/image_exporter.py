#! /usr/bin/python3

import json
import pika
import time
import io
import piexif

import numpy as np
import cv2

null_exif = {
    '0th': {},
    'Exif': {},
    'GPS': {},
    'Interop': {},
    '1st': {},
    'thumbnail': None
}

copy_right = 'Waggle (http://wa8.gl) and Array of Things (https://arrayofthings.github.io). Do not use without explicit permission'
datetime_format = '%Y-%m-%d %H:%M:%S'

EXCHANGE = 'image_pipeline'
ROUTING_KEY_EXPORT = 'exporter'


def generate_meta_data(meta_data, results):
    exif_dict = null_exif.copy()
    oth = exif_dict['0th']
    if 'image_width' in meta_data:
        oth[piexif.ImageIFD.ImageWidth] = int(meta_data['image_width'])
    if 'image_height' in meta_data:
        oth[piexif.ImageIFD.ImageLength] = int(meta_data['image_height'])
    if 'node_id' in meta_data:
        oth[piexif.ImageIFD.Make] = meta_data['node_id']
    if 'device' in meta_data:
        oth[piexif.ImageIFD.Artist] = meta_data['device']
    if 'producer' in meta_data:
        oth[piexif.ImageIFD.Software] = meta_data['producer']
    if 'timestamp' in meta_data:
        timestamp = meta_data['timestamp']
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        oth[piexif.ImageIFD.DateTime] = time.strftime(datetime_format, time.gmtime(timestamp))
    if 'processing_software' in meta_data:
        oth[piexif.ImageIFD.ProcessingSoftware] = meta_data['processing_software']
        oth[piexif.ImageIFD.Copyright] = copy_right
    exif_dict['0th'] = oth

    exif = exif_dict['Exif']
    if results != []:
        exif[piexif.ExifIFD.UserComment] = json.dumps({'results': results}).encode()
    exif_dict['Exif'] = exif

    return exif_dict


def convert_image_to_jpg(image, pixelformat='MJPG'):
    jpeg_binary = None
    if 'MJPG' in pixelformat:
        nparr = np.fromstring(image, np.uint8)
        np_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        jpeg_binary = cv2.imencode('.jpg', np_image)[1].tostring()
    else:
        raise Exception('Unsupported image format %s' % (pixelformat,))
    return jpeg_binary


def make_image_bytes(meta_data, additional_info, image):
    ret = io.BytesIO()
    try:
        exif = generate_meta_data(meta_data, additional_info)
        image_format = meta_data['image_format'].upper()
        if image_format != 'JPEG' or image_format != 'JPG':
            image = convert_image_to_jpg(image, image_format)
        exif_bytes = piexif.dump(exif)
        piexif.insert(exif_bytes, image, ret)
        return ret.read()
    except Exception as ex:
        if 'processing_software' in meta_data:
            software = meta_data['processing_software']
            print('Could not process the image from %s: %s' % (software, str(ex)))
        else:
            print('Could not process image: %s' % (str(ex),))
    return None


def process_image(channel, method, properties, body):
    if properties.headers != {}:
        headers = properties.headers
        if 'results' in headers:
            processed_data = headers['results']
        else:
            processed_data = []
        jpeg_binary = make_image_bytes(headers, processed_data, body)
        if jpeg_binary is not None:
            properties = pika.BasicProperties(
                headers=headers,
                delivery_mode=2,
                timestamp=int(time.time() * 1000),
                content_type='b',
                type='jpeg',
                app_id='image_exporter:0:0',
            )
            channel.basic_publish(
                exchange='',
                routing_key='images',
                body=jpeg_binary,
                properties=properties
            )
            print("pushing image to export queue...")
    else:
        print("The message does not have header to parse...")


def main():

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='direct', durable=True)
    queue = channel.queue_declare(exclusive=True)

    # Binding consistently fails on a clean RMQ broker unless
    # a small delay is introduced between declarations and binding
    time.sleep(1)

    channel.queue_bind(
        exchange=EXCHANGE,
        queue=queue.method.queue,
        routing_key=ROUTING_KEY_EXPORT)
    channel.queue_declare(queue='images', arguments={'x-max-length': 32})

    channel.basic_consume(process_image, queue=queue.method.queue, no_ack=True)
    try:
        channel.start_consuming()
    except (KeyboardInterrupt, Exception) as ex:
        print(str(ex))
        channel.stop_consuming()
    finally:
        channel.close()
        connection.close()


if __name__ == '__main__':
    main()
