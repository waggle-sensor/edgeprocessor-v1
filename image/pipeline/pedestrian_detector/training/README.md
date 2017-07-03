# Trainer for pedestrian detection

This document covers 1) collections of positive and negative images by cropping from sample images, 2) training a classifier, and 3) performing hard-negative-mining of the classifier.

# Requirements

* OpenCV 3.2.0 or higher (including Python wrapper)
* A Waggle camera

# Steps

## Collect sample images

Take images from an attached Waggle camera. Collecting more than 1,000 images is advised. As a person manually does a cropping job to annotate positive images from the sample images, the sample images would need to be resized to fit to the screen for the person to see them for the job. Do the following,

```bash
$ crop_img.py --images=/PATH/TO/SAMPLE_IMAGES --out=/PATH/TO/POSITIVE_IMAGES
```

Drag & drop a mouse on the image to select the region of positive image (i.e., pedestrian). When the light green box well surrounds the pedestrian, press __c__ to crop and save. The cropped image will be resized into 64 X 128 (width x height) and stored into the path of positive images. To 