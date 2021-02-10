import logging
import sys
from backupmanager.integration_tests.it_base import ITBase

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

class ITBackupManager(ITBase):

    def setup(self):
        logger.info('Running setup')
        self.setup_base()

    def test_something(self):
        print('test_something')
        pass