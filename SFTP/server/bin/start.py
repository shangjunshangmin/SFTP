# -*- coding: utf-8 -*-
__author__ = 'JUN SHANG'
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from SFTP.server.core.main import Manage

if __name__ == '__main__':
    Manage().run()
