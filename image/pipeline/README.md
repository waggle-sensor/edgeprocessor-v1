# Processors on the Edge

Any processors running on Edge processor have to follow the rules and constraints in the pipeline, not only for avoding any issues with other processors but also being able to process data properly.

## Minimum requirements for a processor

* The pipeline is powered by RabbitMQ such that a processor will need RabbitMQ client library in their prefered programming language. We recommend the following tools (Note that JAVA is not currently supported by Waggle)

[Python](https://pypi.python.org/pypi/pika)
[C++](https://github.com/alanxz/rabbitmq-c)
