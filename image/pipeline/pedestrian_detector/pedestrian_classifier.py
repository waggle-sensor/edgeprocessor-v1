import cv2
import numpy as np
import time

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)

model = cv2.ml.SVM_load('model_linear.xml')
vector = model.getSupportVectors()
vector = vector.transpose()
# vector = np.append(vector, vector[-1])
print(len(vector), type(vector))

de = cv2.HOGDescriptor_getDefaultPeopleDetector()
print(len(de), type(de))
hog = cv2.HOGDescriptor()
hog.setSVMDetector(vector)

def inside(r, q):
    rx, ry, rw, rh = r
    qx, qy, qw, qh = q
    return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh


def draw_detections(img, rects, thickness = 1):
    for x, y, w, h in rects:
        # the HOG detector returns slightly larger rectangles than the real objects.
        # so we slightly shrink the rectangles to get a nicer output.
        pad_w, pad_h = int(0.15*w), int(0.05*h)
        cv2.rectangle(img, (x+pad_w, y+pad_h), (x+w-pad_w, y+h-pad_h), (0, 255, 0), thickness)

FPS = 1/2 # 15 frames per second
t = time.time()

while True:
    try:
        current_time = time.time()
        if current_time - t > FPS:
            t = current_time
            f, frame = cap.read()
            # cv2.imshow('image', frame)
            if f:
                found, w = hog.detectMultiScale(frame, winStride=(8, 8), padding=(32, 32), scale=1.10)
                # found_filtered = []
                # for ri, r in enumerate(found):
                #     for qi, q in enumerate(found):
                #         if ri != qi and inside(r, q):
                #             break
                #     else:
                #         found_filtered.append(r)
                draw_detections(frame, found)
                # print('%d (%d) found' % (len(found_filtered), len(found)))
                print('%d found' % (len(found),))
                # cv2.imshow('image', frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        break

cap.release()

# EXCHANGE = 'image_pipeline'
# ROUTING_KEY_RAW = '0'
# ROUTING_KEY_OUT = '1'
# ROUTING_KEY_EXPORT = '9'
#
# connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
# channel = connection.channel()
#
# result = channel.queue_declare(exclusive=True)
# my_queue = result.method.queue
#
# def on_process(ch, method, props, body):
#     try:
#         message = json.loads(body.decode())
#         base64_image = message['image'].encode()
#         image = base64.b64decode(base64_image)
#
#         # Calculate average color of the image
#         avg_color = str(get_average_color(image))
#         results = message['results']
#         results.append({'avg_color': avg_color})
#         message['results'] = results
#
#         # Export the image along with the information
#         channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY_EXPORT, body=json.dumps(message))
#     except Exception as ex:
#         print(ex)
#
# channel.queue_bind(queue=my_queue, exchange=EXCHANGE, routing_key=ROUTING_KEY_RAW)
#
# channel.basic_consume(on_process, queue=my_queue, no_ack=True)
# try:
#     channel.start_consuming()
# except:
#     channel.stop_consuming()