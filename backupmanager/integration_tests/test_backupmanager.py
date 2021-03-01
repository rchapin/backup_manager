import logging
import os
import sys
import yaml
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
        '''
        Generate some test data that we will rsync to the docker container, and
        build a dict that stores paths and sizes of the files.
        '''
        expected_files = []
        d1 = os.path.join(ITBase.test_configs.test_data_dir, 'd1')
        f1_path, f1_size = IntegrationTestUtils.create_test_file(d1, 'f1.txt', 256)
        f1_expected_path = os.path.join('/data/d1/', 'f1.txt')
        expected_files.append(dict(expected_path=f1_expected_path, expected_size=f1_size))

        d2 = os.path.join(ITBase.test_configs.test_data_dir, 'd1', 'd2')
        f2_path, f2_size = IntegrationTestUtils.create_test_file(d2, 'f2.txt', 1024)
        f2_expected_path = os.path.join('/data/d1/d2', 'f2.txt')
        expected_files.append(dict(expected_path=f2_expected_path, expected_size=f2_size))

        jobs = []
        job = {}
        job['id'] = 'local_to_container'
        job['user'] = 'root'
        job['host'] = ITBase.test_configs.test_host
        job['port'] = ITBase.test_configs.container_port

        # Create lock file on the localhost
        lock_files = []
        lock_files.append(dict(
            type='local',
            path=os.path.join(ITBase.test_configs.lock_dir, 'lock_file'),
            ))
        job['lock_files'] = lock_files

        syncs = []
        syncs.append(dict(
            source=d1,
            dest='/data',
            opts=['-av', '--delete'],
            ))
        job['syncs'] = syncs
        jobs.append(job)

        configs = IntegrationTestUtils.build_base_config(ITBase.test_configs)
        configs['jobs'] = jobs
        configs['cron_schedule'] = '* * * * *'

        config_path = os.path.join(ITBase.test_configs.config_dir, ITBase.test_configs.config_file)
        IntegrationTestUtils.write_yaml_file(config_path, configs)

