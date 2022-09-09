<!--
waggle_topic=/edge_processor/introduction
-->

# _This repo is archived. See https://github.com/waggle-sensor/edgeprocessor_

# Node Stack - Edge Processor Repo

This repo contains software and tools specific to the edge processor, covering functionality such as:

* Installing required audio / video processing dependencies.
* Operating the image pipeline.

Note that this software was originally targetting the ODROID XU4, so some components may require
significant tweaks before running them on other devices.

## Setup

First, we assume that the [core](https://github.com/waggle-sensor/core) repo has already been set up on a device.

The edge processor dependencies and services can then be installed and configured by running:

```sh
git clone https://github.com/waggle-sensor/edge_processor /usr/lib/waggle/edge_processor
cd /usr/lib/waggle/edge_processor
./configure
```

## Image Pipeline

Plugins deployed on the edge processor interface with the image pipeline to get images. An in-depth description
can be found [here](image/README.md).
