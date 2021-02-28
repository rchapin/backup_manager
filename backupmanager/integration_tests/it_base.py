from invoke import run
import logging
import unittest
import os
import sys
from backupmanager.integration_tests.int_test_utils import IntegrationTestUtils

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

DOCKER_SSH_WAIT_TIME = 1

class ITBase(unittest.TestCase):

    env_vars = None
    test_configs = None

    def build_config(self):
        pass

    @classmethod
    def setUpClass(cls):
        ITBase.test_configs = IntegrationTestUtils.read_env_vars();

    def run_backup_manager(self):
        pass

    def setup_base(self):
        logger.info('Running setup_base')
        pass

    def tear_down(self):
        IntegrationTestUtils.stop_docker_container(ITBase.test_configs)
