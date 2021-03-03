import getpass
import logging
import os
from pathlib import Path, PurePath
import sys
import unittest
from backupmanager.integration_tests.it_base import ITBase
from backupmanager.lib.utils import Utils

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

TEST_PID_PARENT_DIR = '/var/tmp/'
TEST_PID_FILE_NAME = 'test_pid'

class UtilsTest(ITBase):

    def clean_up_test_pid(self, path):
        pass

    def get_write_pid_config(self, pid_file_dir):
        '''
        For all of the write_pid tests we only need the most minimum of a config
        file .
        '''
        return dict(pid_file_dir=TEST_PID_PARENT_DIR)

    def write_test_pid(self, pid=None):
        current_user = getpass.getuser()
        pid_file_dir = os.path.join(TEST_PID_PARENT_DIR, current_user)
        Path(pid_file_dir).mkdir(parents=True, exist_ok=True)
        pid_file_name = f'backupmanager-test_write_pid-{current_user}.pid'
        pid_file_path = os.path.join(pid_file_dir, pid_file_name)
        if pid:
            with open(pid_file_path, 'w') as fh:
                fh.write(str(pid))
        else:
            Path(pid_file_path).touch()

        return pid_file_dir, pid_file_name

    def test_write_pid_finds_existing_file_with_our_pid(self):
        # Write out a pid file with our pid.
        our_pid = os.getpid()
        pid_file_name = self.write_test_pid(our_pid)
        actual_result = Utils.write_pid(logger, self.get_write_pid_config(), pid_file_name)
        print('foo')
