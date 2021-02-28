from collections import namedtuple
from fabric import Connection
from invoke import Collection, task, exceptions, run
import logging
import os
import sys
import time

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
    def get_test_docker_conn(env_vars):
        return Connection(
            host=env_vars[''],
            user='root',
            port=env_vars['BACKUPMGRINTTEST_CONTAINER_PORT'],
            key_filename=env_vars['BACKUPMGRINTTEST_SSH_IDENTITY_FILE_PUB'])

    @staticmethod
    def is_docker_container_running(configs):
        result = run(f"docker ps | grep {configs.image_name}", warn=True)
        if result.ok:
            return True
        else:
            return False

    @classmethod
    def read_env_vars(cls):
        attributes_list = []
        values = []
        for k, v in os.environ.items():
            if ENV_VAR_PREFIX in k:
                '''
                Generate an attribute name for the namedtuple by removing the
                the prefix from the key and converting it to lower-case.
                '''
                key = k.replace(f'{ENV_VAR_PREFIX}_', '').lower()
                attributes_list.append(key)
                values.append(v)

        attributes = ' '.join(attributes_list)
        test_conf = namedtuple(TEST_CONF_NAMED_TUPLE, attributes)

        '''
        Sort the list to print log message.  DO NOT sort prior to generating
        the attributes string or the order of the attribute names and values
        will not be correct.
        '''
        attributes_list.sort()
        logger.info(f'Generating TestConfigs namedtuple with attributes={attributes_list}')
        retval = test_conf(*values)
        logger.info(f'Returning TestConfigs={retval}')
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
