# edge_processor/image/producer
service that captures images from the cameras and sends them to the images fanout exchange

## RabbitMQ-Based Messaging Architecture ##

The image producer creates an "image_pipeline" fanout exchange where it pushes images for consumption by the image processing pipeline. Each image is wrapped in the following simple JSON structure:
```
{ 'results':[<epoch time of capture>,], 'image':<binary image blob> }
```

The __results__ array element contains analysis result strings for each stage of the pipeline. In this case, the relevant result is the timestamp of the capture. The __image__ element contains a base64 string representation of the binary image data.