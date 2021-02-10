import logging
import unittest
import os
import sys

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

    def build_config(self):
        pass

    def run_backup_manager(self):
        pass