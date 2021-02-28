import logging
import os
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
        configs = IntegrationTestUtils.build_base_config(ITBase.test_configs)
        jobs = []
        job = {}
        job['id'] = 'local_to_container'
        job['user'] = 'root'
        job['host'] = ITBase.test_configs.test_host
        job['port'] = ITBase.test_configs.container_port

        # Create lock file on the localhost
        lock_files = dict(
            type='local',
            path=os.path.join(ITBase.test_configs.lock_dir, 'lock_file'),
            )

        syncs = dict(
            )



