from invoke import run
import logging
import unittest
import os
import shutil
import sys
from backupmanager.integration_tests.int_test_utils import IntegrationTestUtils
from backupmanager.lib.backupmanager import BackupManager

logging.basicConfig(
    format="%(asctime)s,%(levelname)s,%(module)s,%(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

DOCKER_SSH_WAIT_TIME = 1


class ITBase(unittest.TestCase):
    def run_backup_manager(self, config_path, expected_files):
        args = self.get_default_args()
        backupmanager = BackupManager(args)
        backupmanager.run()
        self.validate_post_contitions(expected_files)

    def build_config(self, cron_schedule="* * * * *", jobs=None):
        retval = {}
        retval["pid_file_dir"] = self.test_configs.pid_dir
        retval["cron_schedule"] = cron_schedule
        retval["rsync_impl"] = "linux_native"
        if jobs:
            retval["jobs"] = jobs
        return retval

    def build_job_config(self):
        pass

    def get_default_args(self, loglevel="info", dryrun=False):
        config_path = os.path.join(
            self.test_configs.config_dir, self.test_configs.config_file
        )
        return dict(
            configfile=config_path,
            dryrun=dryrun,
            loglevel=loglevel,
        )

    def setup_base(self):
        logger.info("Running setup_base")
        self.test_configs = IntegrationTestUtils.get_test_configs()

        # Clean any test dirs if they exist and then recreate them
        test_dirs = [
            self.test_configs.config_dir,
            self.test_configs.lock_dir,
            self.test_configs.pid_dir,
            self.test_configs.test_data_dir,
        ]
        for d in test_dirs:
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d, exist_ok=True)

    def tear_down(self):
        IntegrationTestUtils.stop_docker_container(self.test_configs)

    def validate_post_contitions(self, expected_files):
        logger.info("Validating post conditions")
        """
        Iterate over each of the extected files dicts and ensure that there is
        a file in the path specified that is the specified size in bytes.
        """
        conn = IntegrationTestUtils.get_test_docker_conn(self.test_configs)
        for expected_file in expected_files:
            # Get the size from an expected path
            expected_path = expected_file["expected_path"]
            result = conn.run(f"stat -c '%s' {expected_path}", warn=True)
            if result.ok:
                actual_size = int(result.stdout.strip())
                expected_size = expected_file["expected_size"]
                self.assertEqual(
                    expected_size,
                    actual_size,
                    f"expected_path={expected_path} expected_size={expected_size} != actual_size={actual_size}",
                )
            else:
                self.fail(f"expected_path={expected_path} was not found")
