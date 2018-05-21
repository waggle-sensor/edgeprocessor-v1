<!--
waggle_topic=Waggle/Node/Edge Processor
-->

# Image pipeline on Edge Processor

## Pipeline architecture

![Image pipeline architecture](pipeline_benchmark/resources/pipeline.png)

A frame is captured by `waggle-image-producer` and is pushed into an exchange called `image_pipeline` in the local RMQ broker. Any processor, subscribing to the exchange, can receive images. The frame may be modified, by the process and put back in the exchange, wherein the routing-key is modified to signify manipulation. Whenever the frame is ready to be transferred to Beehive, it is put in the exchange with the routing-key `exporter`. The `waggle-image-exporter` service moves the frame to `images` queue. The frames in the `images` queue are asynchronously shipped (best-effort) to beehive by a shovel in NodeController.

The images are shoved into the RMQ images exchange on beehive, and the subscribers of the exchange recieve them. The frames are JPEGformat, with Meta-data stored in the EXIF tags. The meta-data can be acquired by unpacking the EXIF header. 

Waggle 2.8.2 or greater _supports_ EXIF tag feature. Former Waggle nodes with version 2.8.1 or less send images using the following format,
```
{'results':[{'timestamp':timestamp,'node_id':node_id,'cam_location':cam_location},], 'image':image}
```
To access raw JPEG image, use `image` key in the message. Use `results` key for the meta-data of the image.

## Topic (Routing key in RabbitMQ syntax)
The image pipeline is designed to accommodate re-publishing a image into the exchange for further manipulations on the image. User plugins use topics to subscribe and publish images. User plugins are also able to create topic as needed (Refer to the example 2 in the above figure). Topic name normally starts with alpabet and can contain numbers and some of special characters such as `.`, `/`, `-`, `_`, and so on. No use of capital alphbet is recommended.

There are reserved topics (i.e., routing keys) that plugins or applications __must not__ use to publish,
* __top__ is used to publish images captured from Waggle Top Camera
* __bottom__ is used to publish images captured from Waggle Bottom Camera
* __export__ is used to subscribe images that are being exported to Beehive

## Message format
As user plugins begin receiving and publishing messages within image pipeline on Edge Processor, the plugins will need to interpret those messages correctly. Since Waggle software has been rapidly evolved to accommodate a raw image along with various types of information, there is a few message formats based on Waggle version. The following sub-sections will cover each format such that user plugins know how to handle messages from image pipeline.

_NOTE: for Waggle 2.8.2 or greater, messages that are exported to outside of Edge Processor are a metadata-embedded JPEG image, and thus the following formats are only valid within image pipeline except Format 1; former Waggles less then 2.8.2 still use Format 1 shown below, even after message is exported_

### Format 1 (Prior to Waggle 2.8.2)
The message is JSON format plain text as follows,
```
{'results':[{'timestamp':timestamp,'node_id':node_id,'cam_location':cam_location},], 'image':image}
```
where `timestamp` is integer type epoch time when the image was captured, `node_id` is NodeController's id, `cam_location` is a string indicating source of the image. `image` is base64 encoded JPEG image. To get raw JPEG image,
```
#! /usr/bin/python3
import base64
# image is "b'CONTENTS'" so b' and ' need to be removed
jpg_image = base64.b64decode(image[2:-1])
```

### Format 2 (On Waggle 2.8.2)
Message content is an instance of a custom Python class [Packet](https://github.com/waggle-sensor/edge_processor/blob/944ae2979c39ea76611af7f86a1e4f48901fc7d4/image/processor.py#L10). A packet consists of 3 parts: meta data, result, and image. Meta data includes the followings,
* `node_id`: node_id
* `image_width`: width of the image
* `image_height`: height onf the image
* `device`: device used to capture the image
* `producer`: name of the program that produced the image
* `datetime`: datetime when the image was captured (format is '%Y-%m-%d %H:%M:%S')

Result is an array that sequentially accumulates results produced by user plugins. Image is base64 encoded JPEG image. However, `load` function on the Packet class provides base64 decoding such that user plugin will not need to decode itself.

### Format 3 (Waggle 2.9.0 or greater)
In this format, message actively uses RabbitMQ properties. Message body contains only image. Format of image is MJPG (Motion JPEG) and may need to be converted for image manipulations. Code snippet for the conversion is,
```
import numpy as np
import cv2
properties, image = get_message()
nparr_img = np.fromstring(image, np.uint8)
img = cv2.imdecode(nparr_img, cv2.IMREAD_COLOR)
```

Message headers (through RabbitMQ.properties.headers) store meta data of image. Meta data includes,
* `node_id`: node_id
* `image_width`: width of the image
* `image_height`: height of the image
* `image_format`: image format (default is MJPG)
* `image_size`: size of the image in byte
* `image_rotate`: orientation of the image; rotate the image as much as the value to see the image in right orientation
* `device`: device used to capture the image
* `producer`: name of the program that produced the image
* `timestamp`: string formatted epoch time

User plugins are welcome to add more header properties such as `results`. However, when the message is sent to be exported, only pre-defined properties will be encoded using EXIF and included in the image. Pre-defined properties include `processing_software` as well as all the properties listed above.

## Supported libraries
Please refer to [supported_libraries](supported_libraries_in_waggle.md)