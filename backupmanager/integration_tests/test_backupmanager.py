import unittest
import logging
import os
import sys
from fabric import Connection
from backupmanager.integration_tests.it_base import ITBase
from backupmanager.integration_tests.int_test_utils import IntegrationTestUtils, AppConfigs, Job, LockLocal, LockRemote, BlocksOnLocal, BlocksOnRemote, Sync
from backupmanager.integration_tests.int_test_utils import AppConfigs
from backupmanager.lib.backupmanager import BackupManager
from backupmanager.lib.backupmanager import PID_FILE_NAME

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

class ITBackupManager(ITBase):

    def setUp(self):
        logger.info('Running setup')
        self.setup_base()
        IntegrationTestUtils.restart_docker_containter(self.test_configs)

    def tearDown(self):
        self.tear_down()

    # @unittest.skip('skip')
    def test_will_shutdown_when_finding_an_existing_pid_file_that_is_not_our_pid(self):
        # Get our pid and then write out a pid file with a different pid
        our_pid = os.getpid()
        pid_file_path = os.path.join(self.test_configs.pid_dir, PID_FILE_NAME)
        with open(pid_file_path, 'w') as fh:
            other_pid = str(our_pid + 31)
            # Include a trailing carriage return
            fh.write(other_pid)

        lock_files = [LockLocal(type="local", path=os.path.join(self.test_configs.lock_dir, "sync.lock"))]
        syncs = [Sync(source="/var/tmp/somedir", dest="/var/tmp/some_other_dir", opts=None)]
        jobs = [Job(id="job-id-1", user="root", host="other_host", port=None, lock_files=lock_files, blocks_on=None, syncs=syncs)]
        app_configs = AppConfigs(cron_schedule="30 * * * *", jobs=jobs)
        IntegrationTestUtils.build_test_configs(app_configs)

        jobs = []
        jobs.append()
        configs = self.build_config()
        IntegrationTestUtils.write_configs(self.test_configs, configs)
        args = self.get_default_args()
        backupmanager = BackupManager(args)
        backupmanager.run()


    # @unittest.skip('skip')
    def test_something(self):
        logger.info('test_something')
        '''
        Generate some test data that we will rsync to the docker container, and
        build a dict that stores paths and sizes of the files.
        '''
        expected_files = []
        d1 = os.path.join(self.test_configs.test_data_dir, 'd1')
        f1_path, f1_size = IntegrationTestUtils.create_test_file(d1, 'f1.txt', 256)
        f1_expected_path = os.path.join('/data/d1/', 'f1.txt')
        expected_files.append(dict(expected_path=f1_expected_path, expected_size=f1_size))

        d2 = os.path.join(self.test_configs.test_data_dir, 'd1', 'd2')
        f2_path, f2_size = IntegrationTestUtils.create_test_file(d2, 'f2.txt', 1024)
        f2_expected_path = os.path.join('/data/d1/d2', 'f2.txt')
        expected_files.append(dict(expected_path=f2_expected_path, expected_size=f2_size))

        jobs = []
        job = {}
        job['id'] = 'local_to_container'
        job['user'] = 'root'
        job['host'] = self.test_configs.test_host
        job['port'] = self.test_configs.container_port

        # Create lock file on the localhost
        lock_files = []
        lock_files.append(dict(
            type='local',
            path=os.path.join(self.test_configs.lock_dir, 'lock_file'),
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

        configs = IntegrationTestUtils.build_base_config(self.test_configs)
        configs['jobs'] = jobs
        configs['cron_schedule'] = '* * * * *'

        config_path = os.path.join(self.test_configs.config_dir, self.test_configs.config_file)
        IntegrationTestUtils.write_yaml_file(config_path, configs)

        self.run_backup_manager(config_path, expected_files)
