<!--
waggle_topic=IGNORE
-->

# edge_processor/image/producer
service that captures images from the cameras and sends them to the images fanout exchange

## RabbitMQ-Based Messaging Architecture ##

The image producer creates an "image_pipeline" fanout exchange where it pushes images for consumption by the image processing pipeline. Each image is wrapped in the following simple JSON structure:
```
{ 'results':[<producer data dict>,], 'image':<binary image blob> }
```
where the data dict has the following form:
```
{'timestamp':<timestamp>,'node_id':<node_id>,'cam_location':<'top', 'bottom', etc...>}
```

The __results__ array element contains analysis result strings for each stage of the pipeline. In this case, the relevant results are the timestamp of the capture, Node ID (derived from Node Controller MAC address), and the camera position with respect to the node body. The __image__ element contains a base64 string representation of the binary image data.

## AoT Camera Resolutions ##
top: 3264x2448, 2592x1944, 2048x1536, 1600x1200, 1280x960, 1024x768, 800x600, 640x480, 320x240
bottom: 2592x1944, 2048x1536, 1920x1080, 1600x1200, 1280x1024, 1024x768, 800x600, 640x480, 320x240

## AoT Data Rate Calculation ##
Using a fswebcam compression factor of 90, a top camera image at 1024x768 is about 53K. A bottom camera image at 1920x1080 is about 511K. It is reasonable to sacrifice top camera resolution to increase bottom camera resolution since top camera images of the sky do not have a lot of fine details. If we limit to an image per camera every 30 minutes we will transfer about 0.81G per month. Any more than that and we risk going over the 1G per month limit on our AT&T data plan.
