# -*- coding: utf-8 -*-
__author__ = 'JUN SHANG'
import os

HOST = "127.0.0.1"  #
PORT = 22
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNT_FILE=os.path.join(BASE_DIR,'db','account.ini')
MAX_concurrent_COUNT=10