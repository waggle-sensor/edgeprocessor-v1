# Trainer for pedestrian detection

This document covers 1) collections of positive and negative images by cropping sample images, 2) training a classifier, and 3) performing hard-negative-mining for the classifier.

# Requirements

* OpenCV 3.2.0 or higher (including Python wrapper)
* A Waggle camera

# Steps

1. Collect sample images

Take images from an attached Waggle camera. Collecting more than 1,000 images is advised. As a person manually does a cropping job to annotate positive images from the sample images, the sample images would need to be resized to fit to the screen for the person to see them for the job. Do the following,

```bash
$ crop_images.py --image=/PATH/TO/SAMPLE_IMAGES --out=/PATH/TO/POSITIVE_IMAGES --screen-width=1380 --screen-height=768
```

An OpenCV window will appear to show the sample images. Drag & drop a mouse on the image to select the region of positive image, i.e. pedestrian. When the light green box well surrounds the pedestrian, press __c__ to crop and save. The cropped image will be resized into 64 X 128 (width x height) and stored into the path of positive images. After cropping all pedestrians of the image, press __q__ to go next. Pressing __r__ clears any selected regions.

Put non-scaled images that have no pedestrian into the /PATH/TO/NEGETIVE_IMAGES. Putting different images in terms of angle, brightness, shade is advised.

2. Run trainer for classifier

First of all, make files that respectively contain a list of positive and negative images.

```bash
$ ls /PATH/TO/POSITIVE_IMAGES > pos.lst
$ mv pos.lst /PATH/TO/POSITIVE_IMAGES
$ ls /PATH/TO/NEGATIVE_IMAGES > neg.lst
$ mv neg.lst /PATH/TO/NEGATIVE_IMAGES
```

To train a classifier for pedestrian detection,

```bash
$ cd /PATH/TO/TRAINER
$ ./trainer.py -pd=/PATH/TO/POSITIVE_IMAGES/ -p=pos.lst -nd=/PATH/TO/NEGATIVE_IMAGES/ -n=neg.lst
$ ls -l my_people_detector.yml 
-rw-rw-r-- 1 waggle waggle 130643864 Jul  3 13:29 my_people_detector.yml
$ cp my_people_detector.yml /PATH/TO/PEDESTRIAN_CLASSIFIER
```

3. Test the classifier

Test the classifier and collect results

```bash
$ cd /PATH/TO/PEDESTRIAN_CLASSIFIER
$ ./pedestrian_classifier.py -c=my_people_detector.yml
// or
$ systemctl (re)start waggle-image-pedestrian-detector.service
```

4. Hard-negative mining (Optional)

If the results of the detection contain many false positives, meaning that the detector recognized things that are actually not pedestrian, hard-negative mining is required for the classifier.