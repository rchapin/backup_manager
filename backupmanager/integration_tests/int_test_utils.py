from collections import namedtuple
from fabric import Connection
from invoke import run
import logging
import os
import random
import string
import sys
import time
import yaml
from backupmanager.lib.utils import Utils
from pickle import NONE

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

TEST_CONF_NAMED_TUPLE = 'TestConfigs'
ENV_VAR_PREFIX = 'BACKUPMGRINTTEST'
WAIT_FOR_DOCKER_SSH_SLEEP_TIME = 1

class IntegrationTestUtils(object):

    @staticmethod
    def build_base_config(configs):
        retval = {}
        retval['pid_file_dir'] = configs.parent_dir
        return retval

    @staticmethod
    def create_test_file(output_dir, file_name, num_chars):
        '''
        Will create a test file with the specified number of random characters.
        '''
        # Create the dir if it does not exist
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, file_name)
        with open(output_path, 'w') as fh:
            data = ''.join(random.choices(string.ascii_uppercase + string.digits, k=num_chars))
            fh.write(data)

        size = os.path.getsize(output_path)
        return output_path, size

    @staticmethod
    def does_file_exist(test_config, path):
        pass

    @staticmethod
    def get_test_docker_conn(test_configs):
        return Connection(
            host=test_configs.test_host,
            user='root',
            port=test_configs.container_port,
            connect_kwargs=dict(key_filename=test_configs.ssh_identity_file)
            )

    @staticmethod
    def is_docker_container_running(configs):
        result = run(f"docker ps | grep {configs.image_name}", warn=True)
        if result.ok:
            return True
        else:
            return False

    @classmethod
    def get_test_configs(cls):
        env_vars = Utils.get_env_vars(ENV_VAR_PREFIX)
        attributes_list = []
        values = []
        for k, v in env_vars.items():
            '''
            Generate an attribute name for the namedtuple by removing the
            the prefix from the key and converting it to lower-case.
            '''
            key = k.replace(f'{ENV_VAR_PREFIX}_', '').lower()
            attributes_list.append(key)
            values.append(v)

        attributes = ' '.join(attributes_list)
        test_conf = namedtuple(TEST_CONF_NAMED_TUPLE, attributes)
        retval = test_conf(*values)

        # Generate a log message of all of the test config values.
        entries = []
        idx = 0
        for attrib in attributes_list:
            entries.append(f'{attrib}:{values[idx]}')
            idx += 1

        entries.sort()
        log_msg = '\n'.join(entries)
        logger.info(f'Generating TestConfigs namedtuple with attributes:\n{log_msg}')
        return retval

    @staticmethod
    def restart_docker_containter(configs):
        pass

    @staticmethod
    def start_docker_container(configs):
        IntegrationTestUtils.stop_docker_container(configs)
        run(
            f"docker run --rm -d --name {configs.container_name} "
            f"-p {configs.container_port}:22 "
            f"{configs.image_name}"
        )
        IntegrationTestUtils.wait_for_docker_ssh(port=configs.container_port)

    @staticmethod
    def stop_docker_container(configs):
        # First see if the container is running
        if IntegrationTestUtils.is_docker_container_running(configs):
            run(f"docker stop {configs.image_name}")

    @staticmethod
    def wait_for_docker_ssh(port):
        while (True):
            result = run(f'nc -v -w 1 localhost {port}', warn=True)
            if not result.ok:
                logger.info(
                    f'Test docker container is not yet listening for ssh connections on port={port}, '
                    f'sleeping for [{WAIT_FOR_DOCKER_SSH_SLEEP_TIME}] seconds'
                    )
                time.sleep(WAIT_FOR_DOCKER_SSH_SLEEP_TIME)
            else:
                logger.info(f'Test docker container is not accepting connections ssh connections on port={port}')
                break

    @staticmethod
    def write_yaml_file(output_path, data):
        with open(output_path, 'w') as fh:
            yaml.dump(data, fh)
