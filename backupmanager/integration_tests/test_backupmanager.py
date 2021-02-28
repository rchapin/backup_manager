import logging
import sys
from invoke import Collection, task, exceptions, run
from fabric import Connection
from backupmanager.integration_tests.it_base import ITBase
from backupmanager.integration_tests.int_test_utils import IntegrationTestUtils

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

class ITBackupManager(ITBase):

    def setUp(self):
        logger.info('Running setup')
        self.setup_base()
        IntegrationTestUtils.start_docker_container(ITBase.test_configs)
        print('foo')

    def tearDown(self):
        self.tear_down()

    def test_something(self):
        logger.info('test_something')
        configs = self.build_config()
