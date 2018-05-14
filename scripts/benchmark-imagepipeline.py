#! /usr/bin/python3

import time
import argparse

from waggle.pipeline import ImagePipelineHandler

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', dest='device', help='device name')
    args = parser.parse_args()

    input_handler = ImagePipelineHandler(args.device)

    # Get frames for 5 seconds
    timeout = 5.

    ret, message = input_handler.read()
    if ret:
        properties, frame = message
        headers = properties.headers
        print('Resolution %dx%d' % (headers['image_width'], headers['image_height']))
    else:
        print('No frames received!')
        exit(0)

    # Wait to stabilize the handler
    time.sleep(5)
    count = 0
    current = time.time()
    while (time.time() - current) <= timeout:
        method, properties, body = input_handler.raw_read()
        if method is not None:
            count += 1

    input_handler.close()
    if count == 0:
        print('No frames received while measuring FPS!')
        exit(0)
    else:
        fps = count / timeout
        print('Frames received in %.3f seconds: %d' % (timeout, count))
        print('FPS %.2f' % (fps,))
