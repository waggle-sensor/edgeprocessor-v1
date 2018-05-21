<!--
waggle_topic=IGNORE
-->

# Image pipeline exporter
Service that pulls fully processed, annotated images from the images exchange and pushes them to the `images` queue where the images in the queue will be forwarded to Beehive via Nodecontroller. The queue size is limited to 32.

## Embedding Meta data
Exporter service produces a EXIF embedded JPEG image binary blob when exporting an image to outside the pipeline. This means that all processed images that arrive at the exporter service should contain their meta data in order for them to be packed correctly. The following table shows what properties are mapped in EXIF,

| RabbitMQ header property | mapped EXIF property |
| ------------- | ------------- |
| image_width  | ImageIFD.ImageWidth |
| image_height  | ImageIFD.ImageLength |
| node_id | ImageIFD.Make |
| device | ImageIFD.Artist |
| producer | ImageIFD.Software |
| timestamp | ImageIFD.DateTime |
| processing_software | ImageIFD.ProcessingSoftware |
| results | ExifIFD.UserComment |

_NOTE: copyright information is included when creating an EXIF_

## Image format
From Waggle 2.9.0, images from `waggle-image-producer` service are Motion JPEG and will be encoded into a JPEG unless intermediate processors changed format of the images. If an intermediate processor encodes the image into JPEG, the processor __MUST__ change value of the property `image_format` from `MJPG` to `JPEG` in the message header. Otherwise, exporter service will attempt to convert and may fail.

In former Waggles ( < 2.9.0), images being transferred in the image pipeline are all JPEG formatted, and thus no conversion is required.
