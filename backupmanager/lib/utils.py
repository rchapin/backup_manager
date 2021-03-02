import os
from pathlib import Path

from fabric import Connection
import yaml

class Utils(object):

    @staticmethod
    def does_pid_file_exist(pid_path):
        path = Path(pid_path)

        if path.is_dir():
            return False, -1

        if path.is_file():
            # Read the existing file and get the pid if there is one
            existing_pid = None
            with open(pid_path, 'r') as fh:
                pid_path_contents = fh.read().strip()
            try:
                existing_pid = int(pid_path_contents)
            except Exception as e:
                # If this fails, we will assume that there isn't a valid process running
                pass



    @staticmethod
    def get_env_vars(prefix):
        retval = {}
        for k, v in os.environ.items():
            if prefix in k:
                retval[k] = v
        return retval

    @staticmethod
    def load_configs(configfile):
        with open(configfile, 'r') as fh:
            return yaml.load(fh, Loader=yaml.FullLoader)

    @staticmethod
    def is_blocked(blocks_on_conf, logger):
        conn = Connection(
            host=blocks_on_conf['host'],
            user=blocks_on_conf['user'] if blocks_on_conf['user'] else 'root',
            port=blocks_on_conf['port'] if blocks_on_conf['port'] else 22)
        # Does the pip file exist?
        result = conn.run(f"ls {blocks_on_conf['pid_path']}", warn=True)
        if not result.ok():
            '''
            The file did not exist in the expected path. We will assume that
            the process on which we were to block is not running.
            '''
            return False
        else:
            '''
            The file does exist.  We need to read the contents of it and
            confirm if the process listed in it is still running
            '''
            result = conn.run(f"cat {blocks_on_conf['pid_path']}", warn=True)
            if not result.ok():
                # FIXME
                pass
            else:
                pid = result.stdout
                logger.info(f'pid={pid}')

    @staticmethod
    def write_pid(configs, pid_file_name):
        our_pid = os.getpid()
        pid_path = os.path.join(configs['pid_file_dir'], pid_file_name)
        success, existing_pid = Utils.does_pid_file_exist(pid_path)
