import logging
import unittest
import sys

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

class ITBase(unittest.TestCase):

    def setup_base(self):
        logger.info('Running setup_base')
        pass

    def run_backup_manager(self):
        pass