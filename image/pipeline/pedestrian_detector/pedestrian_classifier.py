#!/usr/bin/env python3

import cv2
import numpy as np
import os
import time
import argparse
import logging
import pika
import json
import threading

import sys
sys.path.append('../..')
from processor import *

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


def inside(r, q):
    rx, ry, rw, rh = r
    qx, qy, qw, qh = q
    return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh


def draw_detections(image, rects, thickness = 1):
    for x, y, w, h in rects:
        # the HOG detector returns slightly larger rectangles than the real objects.
        # so we slightly shrink the rectangles to get a nicer output.
        pad_w, pad_h = int(0.15*w), int(0.05*h)
        cv2.rectangle(image, (x+pad_w, y+pad_h), (x+w-pad_w, y+h-pad_h), (0, 255, 0), thickness)


def save_outputs(image, detections, output_path, extension='.jpg', image_size=(64, 128)):
    last_file_name_count = len(os.listdir(output_path))
    for x, y, w, h in detections:
        cropped_image = image[y:y+h, x:x+w]
        resized_image = cv2.resize(cropped_image, image_size, interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(output_path, str(last_file_name_count).zfill(5) + extension), resized_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        last_file_name_count += 1


class Classifier(object):
    def __init__(self):
        self.hog = None
        pass

    def load_classifier(self, classifier_path, window_size=(64, 128)):
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        n_bins = 9
        derive_aperture = 1
        win_sigma = 4.
        histogram_norm_type = 0
        l2_hys_threshold = 2.0e-01
        gamma_correction = 0
        n_levels = 64

        self.hog = cv2.HOGDescriptor(window_size, block_size, block_stride, cell_size,
            n_bins, derive_aperture, win_sigma, histogram_norm_type, l2_hys_threshold,
            gamma_correction, n_levels)

        svm_model = cv2.ml.SVM_load(classifier_path)
        rho = np.ones((1, 1), dtype=np.float32)
        rho_value, alpha, svdix = svm_model.getDecisionFunction(0)
        rho[0] = -1 * rho_value
        vector = svm_model.getSupportVectors().transpose()
        vector_rho = np.concatenate((vector, rho))

        self.hog.setSVMDetector(vector_rho)
        return True

    def classify(self, image, win_stride=(8, 8), padding=(32, 32), scale=1.05, final_threshold=2):
        founds, weights = self.hog.detectMultiScale(image, winStride=win_stride, padding=padding, scale=scale, finalThreshold=final_threshold)

        return founds, weights


class PedestrianProcessor(Processor):
    def __init__(self):
        super().__init__()
        self.options = {
        'camera': None,
        'output': None,
        'verbose': False,
        'interactive': False
        }

    def add_processor(self, processor):
        self.processor = processor

    def setValues(self, options):
        self.options.update(options)

    def getValue(self, key):
        if key in self.options:
            return self.options[key]
        else:
            return None

    def perform(self, source):
        if self.processor is not None:
            return self.processor.classify(source)

    def read(self):
        for stream in self.input_handler:
            if stream is None:
                return False, None
            return stream.read()

    def write(self, packet):
        for stream in self.output_handler:
            if stream is None:
                return False
            stream.write(packet.output())
            if self.options['verbose']:
                logger.info('A packet is sent to output')

    def run(self):
        FPS = 0.
        frame = 0
        start_time = time.time()

        cap = None
        if self.options['camera'] is not None:
            cap = cv2.VideoCapture(self.options['camera'])
            
        packet = None
        try:
            while True:
                if cap:
                    f, image = cap.read()
                else:
                    f, packet = self.read()
                    if f:
                        image = cv2.imdecode(packet.raw, 1)
                if f:
                    founds, weights = self.perform(image)
                    if self.options['output']:
                        save_outputs(image, founds, self.options['output'])

                    if len(founds) > 0:
                        if packet:
                            packet.data.append({'pedestrian_detection': [founds.tolist(), weights.tolist()]})
                            self.write(packet)

                    draw_detections(image, founds, thickness=2)
                    if self.options['interactive']:
                        while True:
                            cv2.imshow('result: n to next, q to exit', image)
                            key = cv2.waitKey(30) & 0xFF
                            if key == ord('n'):
                                break
                            elif key == ord('q'):
                                return
                    # else:
                    #     cv2.imshow('result', image)
                    #     cv2.waitKey(1)
                    frame += 1
                else:
                    time.sleep(0.1)

                if self.options['verbose']:
                    end_time = time.time()
                    if end_time - start_time > 1:
                        start_time = end_time
                        logger.info('FPS is %0.2f' % (frame,))
                        frame = 0
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            logger.error(str(ex))


def interpret_options(args):
    processor = PedestrianProcessor()

    if not args.classifier:
        return False, 'No classifier defined', None

    classifier = Classifier()
    if not classifier.load_classifier(args.classifier):
        return False, 'Cannot load classifier %s ' % (args.classifier,), None
    processor.add_processor(classifier)

    instream = None
    if args.rabbitmq_exchange:
        instream = RabbitMQStreamer()
        instream.config(args.rabbitmq_exchange, args.rabbitmq_routing_in, args.rabbitmq_routing_out)
        result, message = instream.connect()
        if result:
            processor.add_handler(instream, 'in-out')
        else:
            return result, 'Cannot run RabbitMQ %s ' % (message,), None

    if instream is None and args.source_camera is None:
        return False, 'Need an input source either from a camera or rabbitmq exchange', None

    options = {
        'camera': args.source_camera,
        'output': args.output_path,
        'verbose': args.verbose,
        'interactive': args.interactive
    }
    processor.setValues(options)

    return True, '', processor


def main():
    parser = argparse.ArgumentParser()

    # Classifier option
    parser.add_argument('-c', dest='classifier', help='Full path of the classifier')
    
    # Input source options
    parser.add_argument('-s', dest='source_camera', help='Camera path')
    parser.add_argument('--rabbitmq-exchange', dest='rabbitmq_exchange', help='Name of exchange for input')
    parser.add_argument('--rabbitmq-routing-input', dest='rabbitmq_routing_in', help='Routing key for input')

    # Output source options
    parser.add_argument('--rabbitmq-routing-output', dest='rabbitmq_routing_out', help='Routing key for output')
    parser.add_argument('-o', dest='output_path', help='Path to save recognized pedestrians')

    # Other options
    parser.add_argument('-v', dest='verbose', help='Verbose', action='store_true')
    parser.add_argument('-i', dest='interactive', help='Path to test images', action='store_true')
    args = parser.parse_args()

    result, message, processor = interpret_options(args)

    if result is False:
        logger.error(message)
        parser.print_help()
        exit(-1)

    processor.run()


if __name__ == '__main__':
    main()