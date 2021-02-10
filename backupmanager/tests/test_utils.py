import logging
import os
import sys
import unittest

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

class UtilsTest(unittest.TestCase):

    def test_something(self):
        logger.info('test_something')
        self.assertEqual(0, 0)