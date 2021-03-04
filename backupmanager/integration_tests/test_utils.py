import logging
import os
from pathlib import Path
import sys
from invoke import run
from backupmanager.integration_tests.it_base import ITBase
from backupmanager.lib.utils import Utils

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

# TEST_PID_PARENT_DIR = '/var/tmp/'
TEST_PID_FILE_NAME = 'test.pid'

class UtilsTest(ITBase):

    def setUp(self):
        logger.info('Running setup')
        self.setup_base()

    def tearDown(self):
        self.tear_down()

    def clean_up_test_pid(self, path):
        pass

    def get_write_pid_config(self):
        '''
        For all of the write_pid tests we only need the most minimum of a config
        file .
        '''
        return dict(pid_file_dir=self.test_configs.pid_dir)

    def write_test_pid(self, pid=None):
        pid_file_path = os.path.join(self.test_configs.pid_dir, TEST_PID_FILE_NAME)
        if pid:
            with open(pid_file_path, 'w') as fh:
                fh.write(str(pid))
        else:
            Path(pid_file_path).touch()
        return pid_file_path

    def test_write_pid_finds_existing_file_with_our_pid(self):
        '''
        The expectation is that we should have a pid file with our pid in it at
        the end of the test.
        '''
        # Write out a pid file with our pid.
        our_pid = os.getpid()
        pid_file_path = self.write_test_pid(our_pid)
        test_data = dict(
            expected_result=True,
            expected_pid=our_pid,
            pid_file_path=pid_file_path,
            )
        self.exec_write_pid_test(test_data)

    def test_write_pid_finds_empty_pid_file(self):
        '''
        The expectation is that we should have a pid file with our pid in it at
        the end of the test.
        '''
        our_pid = os.getpid()
        # Touch a file in the expected location
        pid_file_path = self.write_test_pid()
        test_data = dict(
            expected_result=True,
            expected_pid=our_pid,
            pid_file_path=pid_file_path,
            )
        self.exec_write_pid_test(test_data)

    def test_write_pid_finds_pid_file_with_another_running_pid(self):
        '''
        The expectation is that we should leave the existing pid file alone.
        '''
        # Search for a pid file of another currently running process
        result = run("ps -ef | head -n 10 | tail -n 1 | awk '{print $2}'")
        actual_pid = None
        if result.ok:
            actual_pid = int(result.stdout.strip())
        if actual_pid is None:
            self.fail('Unable to get an actual pid with which we can run the test')

        # Write the pid to the expected pid file
        pid_file_path = self.write_test_pid(actual_pid)
        test_data = dict(
            expected_result=False,
            expected_pid=actual_pid,
            pid_file_path=pid_file_path,
            )
        self.exec_write_pid_test(test_data)

    def test_write_pid_finds_pid_file_with_another_non_existant_pid(self):
        '''
        The expectation is that we should overwrite that pid in the file.
        '''
        '''
        Search for a pid file of another currently running process and
        increment it's value.
        '''
        result = run("pid=$(ps -ef | awk '{print $2}' | sort -n | tail -n 1); pid=$((pid+1)); echo $pid")
        pid_for_non_existant_process = None
        if result.ok:
            pid_for_non_existant_process = int(result.stdout.strip())
        if pid_for_non_existant_process is None:
            self.fail('Unable to generate a mock pid for a process that does not exist')

        our_pid = os.getpid()

        # Write the pid to the expected pid file
        pid_file_path = self.write_test_pid(pid_for_non_existant_process)
        test_data = dict(
            expected_result=True,
            expected_pid=our_pid,
            pid_file_path=pid_file_path,
            )
        self.exec_write_pid_test(test_data)

    def exec_write_pid_test(self, test_data):
        actual_result = Utils.write_pid(logger, self.get_write_pid_config(), TEST_PID_FILE_NAME)
        self.assertEquals(test_data['expected_result'], actual_result)

        # Read the pid out of the file
        with open(test_data['pid_file_path'], 'r') as fh:
            actual_pid = int(fh.read().strip())

        self.assertEquals(test_data['expected_pid'], actual_pid)

