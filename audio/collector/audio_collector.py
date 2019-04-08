#! /usr/bin/python3
# ANL:waggle-license
# This file is part of the Waggle Platform.  Please see the file
# LICENSE.waggle.txt for the legal details of the copyright and software
# license.  For more details on the Waggle project, visit:
#          http://www.wa8.gl
# ANL:waggle-license

import pyaudio
import wave
from pydub import AudioSegment
import json
import pika
import time
import io
import os
import subprocess

copy_right = 'Waggle (http://wa8.gl) and Array of Things (https://arrayofthings.github.io). Do not use without explicit permission.'
datetime_format = '%Y-%m-%d %H:%M:%S'


class SoundCollector(object):
    def __init__(self):
        command = ['arp -a 10.31.81.10 | awk \'{print $4}\' | sed \'s/://g\'']
        self.node_id=str(subprocess.getoutput(command))
        self.device='microphone'
        self.producer=os.path.basename(__file__)
        self.record_time=str(int(time.time()))
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS=  1
        self.RATE = 48000
        self.RECORD_SECONDS = 10
        self.clip = []
        self.WAVE_OUTPUT_FILENAME = "/tmp/audio_clip.wav"

    def connect(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def run(self):      
        try:
            for i in range(0, int((self.RATE / self.CHUNK) * self.RECORD_SECONDS)):
                self.clip.append(self.stream.read(self.CHUNK, exception_on_overflow = False))
        except KeyboardInterrupt:
            print('Interrupted')
        except Exception as ex:
            print(str(ex))

    def write(self):
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.clip))
        wf.close()

    def convert(self):
        AudioSegment.from_wav("/tmp/audio_clip.wav").export("/tmp/audio.mp3", bitrate='128k', parameters=["-ac", "1"] , format="mp3", tags={'artist': self.node_id, 'album': self.device, 'comments': self.record_time, 'title': self.producer, 'copyright':copy_right})
    
    def create_mp3(self):
        self.connect()
        self.run()
        self.close()
        self.write()
        self.convert()

def main():

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='images', arguments={'x-max-length': 32})
    collect_audio = SoundCollector()
    collect_audio.create_mp3()
    with open("/tmp/audio.mp3", mode='rb') as file: # b is important -> binary
        fileContent = file.read()
    print(len(fileContent))
    node_id1 = str(subprocess.getoutput('hostname'))[:-2]
    channel.basic_publish(exchange='', routing_key='images', properties=pika.BasicProperties(reply_to = node_id1, headers={'processing_software': 'audio_collector', 'timestamp' : int(time.time()), 'device':'microphone' }), body=fileContent)
    connection.close()
    


if __name__ == '__main__':
    main()
