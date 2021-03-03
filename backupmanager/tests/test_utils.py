import getpass
import logging
import os
from pathlib import Path, PurePath
import sys
import unittest
from backupmanager.lib.utils import Utils

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

class UtilsTest(unittest.TestCase):

    def test_something(self):
        pass
