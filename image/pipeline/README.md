# Processors on the Edge

Any processors running on Edge processor have to follow the rules and constraints when use the pipeline not only for avoding any issues with other processors, but also being able to process data properly.

## Minimum Requirements for Waggle Image Processor

* The pipeline is powered by RabbitMQ such that any processors will need RabbitMQ client library in their prefered programming language. We recommend the following tools (Note that JAVA is not supported by Waggle 2.8.2 or former)

[Python](https://pypi.python.org/pypi/pika)

[C++](https://github.com/alanxz/rabbitmq-c)

## Example Processor

The example processor provides basic information of a captured frame. The basic information includes average color and normalized (0-255) histogram of R, G, B channels of the frame. The processor runs 24 hours a day and outputs every 5 minutes. Size of the data is approximately 2.6 KB including 1.6 KB of the basic information. The rest 1 KB is from other data such as JPEG meta data, copyright, image width and height, etc. Montly data use would be approximately 44 MB excluding overheads from the pipeline.

The basic information is JSON-formatted string as follows,

```
{'results': [
  {'avg_color': {'b': 126, 'g': 131, 'r': 135}},
  {'histogram': {
    'b': '1004080c111d171514131415151717161515131414151516161715141312111110100f100f0e0e0d0d0d0c0c0c0b0a0a0a0a0a0a0a0a0a0a0a0b0b0c0c0c0d0e0e0f0f1010111111121212121211111111111110101010101010101010101011111213141617191b1c1d1f1e1e1d1c1a1a19191817171515141515141413121212111111121211111110101010100f0f0f0f0e0f0e0e0f0f0e0f0e0e0e0e0f0f0f0e0e0d0d0d0d0c0d0d0d0c0c0c0b0c0c0d0d0d0d0d0e0d0e0e0e0f0f100f101011121313141615151716171817181716151312111111100f0f10101010110f0f0e0d0c0c0d0c0a08050404030303030304040404040407070f0c071407fe',
    'g': '0502020208141b14100e0f1113151616151212121111100f0f101010101110100f0e0d0b0b0b0c0c0b0a09090909090a0a0a0a0b0a0a090909090808080808080909090a0a0a0b0b0c0c0d0d0e0f0f0f0f0f0f0f0f0f0f0e0e0e0d0d0d0d0d0d0d0d0d0d0d0d0e0e0f0f101111121315151617171617191b1d202324221d1a1818171614121211121213131212121111111110100f0e0e0f0f0f0f0f0f0f0e0e0e0f100f0f0e0e0d0d0d0d0e0e0d0c0c0c0c0c0c0d0d0d0d0d0c0d0d0e0e0e0e0e0e0e0f101111131413131416171718161513100f0e0d0b0b0a0b0a09090a0c0d0f0f0e0d0b0a0b0c0b0a0806040303030303030303030304080707060cff',
    'r': '0301030714150f0d0d0f10121312110f0d0d0d0d0c0b0a0a0c0e0e0e0f0e0d0d0b090909090909080807070707070707080809090908080707070606060606060606070707070808080909090a0a0b0b0c0c0d0d0d0e0e0e0e0e0e0e0e0d0d0d0c0c0c0b0c0c0c0c0c0d0d0e0e0f111313141515151617191b1d1d1b19151313131313131211101010100f0f0f0e0e0d0c0d0d0d0d0d0d0c0c0b0b0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0b0c0c0c0c0c0c0c0b0c0b0b0b0b0b0b0a0b0b0b0b0b0b0b0c0d0d0d0e0f0e0f0f0e0e0d0d0c0c0c0c0d0d0e0e0f0f0f101112110f0e0c0c0b0c0b0b0b090807080808090807050403020202030304040bff'}}]
}
```

The arrays in the histogram are HEX-string of 256 bins.

## Image Collector

The image collector samples frames and transfers the samples to Beehive at a pre-defined rate. The configuration is stored in `/wagglerw/waggle/image_collector.conf` and the default is as follows,

```
{'top': {
        'daytime': [('12:00:00', '23:00:00')], # 6 AM to 7 PM in Chicago
        'interval': 3600,                       # every 60 mins
        'verbose': False
    },
 'bottom': {
    'daytime': [('12:00:00', '23:00:00')], # 6 AM to 7 PM in Chicago
    'interval': 1800,                        # every 30 mins
    'verbose': False
 }
}
```

The configuration can be adjusted, but the processor must be re-run after any adjustments.
