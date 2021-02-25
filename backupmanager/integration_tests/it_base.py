from invoke import run
import logging
import unittest
import os
import sys
from os.path import stat

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

ENV_VAR_PREFIX = 'BACKUPMGRINTTEST'

class ITBase(unittest.TestCase):

    env_vars = None
    test_configs = None

    @classmethod
    def setUpClass(cls):
        ITBase.env_vars = ITBase.read_env_vars()

    @staticmethod
    def is_docker_container_running():
        result = run(f"docker ps | grep {ITBase.env_vars['BACKUPMGRINTTEST_IMAGE_NAME']}", warn=True)
        if result.ok:
            return True
        else:
            return False

    @classmethod
    def read_env_vars(cls):
        retval = {}
        for k, v in os.environ.items():
            if ENV_VAR_PREFIX in k:
                retval[k] = v
        return retval

    def setup_base(self):
        logger.info('Running setup_base')
        pass

    def start_docker_container(self):
        self.stop_docker_container()
        run(
            f"docker run --rm -d --name {ITBase.env_vars['BACKUPMGRINTTEST_CONTAINER_NAME']} "
            f"-p {ITBase.env_vars['BACKUPMGRINTTEST_CONTAINER_PORT']}:22 "
            f"{ITBase.env_vars['BACKUPMGRINTTEST_IMAGE_NAME']}"
        )

    def stop_docker_container(self):
        # First see if the container is running
        if ITBase.is_docker_container_running():
            run(f"docker stop {ITBase.env_vars['BACKUPMGRINTTEST_IMAGE_NAME']}")

    def build_config(self):
        pass

    def run_backup_manager(self):
        pass