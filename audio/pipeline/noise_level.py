#! /usr/bin/python3

import os
import time
import json
import subprocess
import argparse

import pika
import pyaudio
import numpy as np

# TODO: There should be a better way to find Waggle microphone
WAGGLE_MICROPHONE_NAME = 'USB PnP Sound Device:'
my_name = os.path.basename(__file__)


def get_default_configuration():
    default_config = {
        'sampling_period': 5,  # in Second
        'interval': 300,  # 5 minutes
    }
    return default_config


# TODO: This should use data pipeline, not image pipeline
class PipelineWriter(object):
    def __init__(self, routing_out, exchange='image_pipeline'):
        self.connection = None
        self.channel = None
        self.out_key = routing_out
        self.exchange = exchange

    def open(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
        return True

    def close(self):
        if self.connection is not None:
            if self.connection.is_open:
                self.connection.close()
            self.connection = None
            self.channel = None

    def is_connected(self):
        if self.connection is not None:
            return self.connection.is_open
        else:
            return False

    def write(self, frame, headers):
        properties = pika.BasicProperties(
            headers=headers,
            delivery_mode=2,
            timestamp=int(time.time() * 1000),
            content_type='b')
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.out_key,
            properties=properties,
            body=frame)


class AudioNoiseCalculator(object):
    def __init__(self, hrf=False, node_id='NO_ID'):
        self.hrf = hrf
        self.node_id = node_id
        self.audio_format = pyaudio.paInt16
        self.audio_channels = 1
        self.audio_rate = 44100
        self.audio_chunk = 1024
        self.config = self._get_config_table()
        self.total_count = int(self.audio_rate / self.audio_chunk * self.config['sampling_period'])
        self.sender = PipelineWriter()
        self.sender.open()

    def _get_config_table(self):
        config_file = '/wagglerw/waggle/audio_noise.conf'
        config_data = None
        try:
            with open(config_file) as config:
                config_data = json.loads(config.read())
        except Exception:
            config_data = get_default_configuration()
            with open(config_file, 'w') as config:
                config.write(json.dumps(config_data, sort_keys=True, indent=4))

        return config_data

    def _read_callback(self, in_data, frame_count, time_info, status):
        self.frames.append(np.frombuffer(in_data, dtype=np.int16))
        # print(frame_count, time_info, status)
        self.frame_count += 1
        if self.frame_count >= self.total_count:
            return (in_data, pyaudio.paComplete)
        else:
            return (in_data, pyaudio.paContinue)

    def _open_and_read(self):
        audio = pyaudio.PyAudio()
        device_count = audio.get_device_count()
        device_index = -1

        for i in range(device_count):
            device_info = audio.get_device_info_by_index(i)
            if WAGGLE_MICROPHONE_NAME in device_info['name']:
                device_index = device_info['index']
                break

        if device_index < 0:
            audio.terminate()
            return None, 'Failed to find Waggle microphone'

        stream = audio.open(
            format=self.audio_format,
            channels=self.audio_channels,
            rate=self.audio_rate,
            input=True,
            frames_per_buffer=self.audio_chunk,
            input_device_index=device_index,
            stream_callback=self._read_callback)

        self.frames = []
        self.frame_count = 0
        stream.start_stream()
        while self.frame_count < self.total_count:
            pass
        stream.stop_stream()
        stream.close()
        audio.terminate()
        return True, self.frames

    def _out(self, data):
        if self.hrf:
            return

        headers = {
            'node_id': self.node_id,
            'image_width': 2,
            'image_height': 1,
            'image_format': 'sBGR',
            'image_size': len(frame),
            'image_rotate': 0,
            'device': 'waggle microphone',
            'producer': my_name,
            'processing_software': my_name,
            'datetime': time.strftime(datetime_format, time.gmtime(time.time()))
        }

        if self.sender.is_connected:
            self.sender.write(message, headers)
        # elif self.sender.

    def close(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio is not None:
            self.audio.terminate()

    def _do_process(self):
        f, raw_data = self._open_and_read()
        if f is False:
            raise Exception(raw_data)
        numpydata = np.hstack(raw_data)

        number_of_samples = numpydata.shape[0]
        time_per_sample = 1.0 / self.audio_rate

        yf = np.fft.fftn(numpydata)  # the n-dimensional FFT
        xf = np.linspace(0.0, 1.0 / (2.0 * time_per_sample), number_of_samples // 2)  # 1.0/(2.0*T) = RATE / 2

        octave = {}
        avg = []
        medium = [31, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]  # Medium? of octave, hearable frequency

        for i in range(10):
            octave[i] = [medium[i]]

        val = yf[0:number_of_samples // 2]

        for idx in range(len(xf)):
            if xf[idx] < 20:
                pass
            elif xf[idx] < 44:
                octave[0].append(val[idx])
            elif xf[idx] < 88:
                octave[1].append(val[idx])
            elif xf[idx] < 176:
                octave[2].append(val[idx])
            elif xf[idx] < 353:
                octave[3].append(val[idx])
            elif xf[idx] < 707:
                octave[4].append(val[idx])
            elif xf[idx] < 1414:
                octave[5].append(val[idx])
            elif xf[idx] < 2825:
                octave[6].append(val[idx])
            elif xf[idx] < 5650:
                octave[7].append(val[idx])
            elif xf[idx] < 11300:
                octave[8].append(val[idx])
            else:
                octave[9].append(val[idx])

        for di in range(len(octave)):
            avg.append(sum(octave[di]) / len(octave[di]))
        # print(octave)
        avg = np.asarray(avg)
        avgdb = 10 * np.log10(np.abs(avg))

        a = []
        b = 0,
        for ia in range(len(avg)):
            a.append(((10 ** (avgdb[ia] / 10)) ** (1 / 2)) * 0.00002)
            b = b + (a[ia] / 0.00002) ** 2

        sdb = 10 * np.log10(b)
        # sdb --> addtion of SPL, avgdb --> average of each octave

        print('Noise level: %0.6f' % (sdb,))
        self._out(sdb)

    def run(self):
        try:
            print('Processing...')
            self._do_process()
            print('Done')
        except Exception as ex:
            print(str(ex))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hrf', action='store_true', help='Print in human readable form')
    args = parser.parse_args()

    command = ['arp -a 10.31.81.10 | awk \'{print $4}\' | sed \'s/://g\'']
    node_id = str(subprocess.getoutput(command))
    if len(node_id) < 1 and args.hrf is False:
        print('No NODE_ID is found. Use --hrf to run without NODE_ID. Abort...')
        exit(1)

    processor = AudioNoiseCalculator(hrf=args.hrf, node_id=node_id)
    processor.run()
