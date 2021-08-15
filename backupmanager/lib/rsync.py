import logging
import sys

logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

class Rsync(object):

    def __init__(self, args):
        logging.getLogger().setLevel(args['loglevel'].upper())

    def linux_native(self):
        pass

    def rsync_manager(self):
        # TODO:
        pass