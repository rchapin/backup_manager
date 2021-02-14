from fabric import Connection

class IntegrationTestUtils(object):

    @staticmethod
    def restart_docker_containter(configs):
        pass

    @staticmethod
    def get_test_docker_conn(env_vars):
        return Connection(
            host=env_vars[''],
            user='root',
            port=env_vars['BACKUPMGRINTTEST_CONTAINER_PORT'],
            key_filename=env_vars['BACKUPMGRINTTEST_SSH_IDENTITY_FILE_PUB'])