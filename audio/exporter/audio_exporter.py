import json
import logging
import os
import os.path
import pika
import time
import io
import base64

import sys
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *