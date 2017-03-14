# edge_processor/image/producer
service that captures images from the cameras and sends them to the images fanout exchange

## RabbitMQ-Based Messaging Architecture ##

The image producer creates an "image_pipeline" fanout exchange where it pushes images for consumption by the image processing pipeline. Each image is wrapped in the following simple JSON structure:
```
{ 'stage':0, 'results':[<epoch time of capture>,], 'image':<binary image blob> }
```

The __stage__ element represents the last stage in the pipeline through which the image proceeded. The __results__ array element contains analysis result strings for each stage of the pipeline. The __image__ element contains the binary image data. In this case, the stage is 0 and the relevant result is the timestamp of the capture.