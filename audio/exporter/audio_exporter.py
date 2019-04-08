# ANL:waggle-license
# This file is part of the Waggle Platform.  Please see the file
# LICENSE.waggle.txt for the legal details of the copyright and software
# license.  For more details on the Waggle project, visit:
#          http://www.wa8.gl
# ANL:waggle-license
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
