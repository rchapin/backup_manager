import logging
import sys
from invoke import Collection, task, exceptions, run
from fabric import Connection
from backupmanager.integration_tests.it_base import ITBase

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

class ITBackupManager(ITBase):

    def setUp(self):
        logger.info('Running setup')
        self.setup_base()
        self.start_docker_container()

    def test_something(self):
        logger.info('test_something')
        configs = self.build_config()

        pass
