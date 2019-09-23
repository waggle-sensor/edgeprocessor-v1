#!/usr/bin/env python3
# ANL:waggle-license
# This file is part of the Waggle Platform.  Please see the file
# LICENSE.waggle.txt for the legal details of the copyright and software
# license.  For more details on the Waggle project, visit:
#          http://www.wa8.gl
# ANL:waggle-license

import sys
import json
import time
import os
import subprocess

import pika


def get_default_configuration():
    default_configuration = {
        'waggle_microphone': {
            'sample_period': 30, # seconds
            'sample_rate': 44100, # hz
            'interval': 60,  # seconds
        },
    }
    return default_configuration


def load_configuration():
    capture_config_file = '/wagglerw/waggle/audio_capture.conf'
    capture_config = None
    try:
        with open(capture_config_file) as config:
            capture_config = json.loads(config.read())
    except Exception:
        pass

    if capture_config is None:
        capture_config = get_default_configuration()
        try:
            with open(capture_config_file, 'w') as config:
                config.write(json.dumps(capture_config, sort_keys=True, indent=4))
        except Exception:
            pass
    return capture_config


def call(command):
    assert isinstance(command, str)
    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output = cmd.communicate()[0].decode().strip()
    return cmd.returncode, output


def get_rmq_connection():
    try:
        connection = pika.BlockingConnection(pika.URLParameters('amqp://localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange='audio_pipeline', exchange_type='direct', durable=True)
        return channel
    except Exception:
        return None


def send_to_rmq(channel, frame, timestamp, headers):
    properties = pika.BasicProperties(
        headers=headers,
        delivery_mode=2,
        timestamp=timestamp,
        content_type='b')

    channel.basic_publish(
        exchange='audio_pipeline',
        routing_key=headers['device'],
        properties=properties,
        body=frame)


def main(target_device):
    return_code, result = call('arecord -l')
    if 'List of CAPTURE Hardware Devices' not in result:
        print('ERROR: No recording device found')
        exit(1)

    feeder = get_rmq_connection()
    if feeder is None:
        print('ERROR: No rabbitmq connection')
        exit(1)

    config = load_configuration()
    if target_device not in config:
        print('ERROR: No configuration for {}'.format(target_device))
        exit(1)
    config = config[target_device]

    sample_rate = config['sample_rate']
    sample_period = config['sample_period']
    interval = config['interval']

    print('INFO: audio procuder started...')
    SUCCESS = 0
    FAILURE = 1
    while True:
        sample_time = int(time.time())
        return_code, result = call('arecord --quiet -f S16_LE -r {} -d {} /tmp/out.wav'.format(sample_rate, sample_period))
        if return_code != SUCCESS:
            print('ERROR: Recording failed - {}'.format(result))
            exit(1)
        return_code, result = call('lame --quiet /tmp/out.wav /tmp/out.mp3')
        if return_code != SUCCESS:
            print('ERROR: Building mp3 failed - {}'.format(result))
            exit(1)

        with open('/tmp/out.mp3', 'rb') as file:
            data = file.read()
            meta_data = {
                'device': target_device,
                'producer': os.path.basename(__file__),
                'audio_rate': sample_rate,
                'audio_period': sample_period,
                'audio_size': len(data),
                'datetime': sample_time
            }

            if feeder.is_closed:
                feeder = get_rmq_connection()
                if feeder is None:
                    print('ERROR: No rabbitmq connection')
                    exit(1)
            send_to_rmq(feeder, data, sample_time, meta_data)

        time.sleep(interval)


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        print('No target device is specified. Exiting...')
        exit(1)
    main()
