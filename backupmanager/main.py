import sys
import logging
import argparse
from backupmanager.backupmanager import BackupManager

# For the time-being, we are just logging to the console
logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--configfile',
        type=str,
        required=True,
        help='Fully qualified path to the config file')

    parser.add_argument(
        '--loglevel',
        type=str,
        default='INFO',
        help='logging output level configuration')

    parser.add_argument(
        '--dryrun',
        action='store_true',
        help='Run in dryrun mode')

    return parser.parse_args()

def main():
    args = parse_args()
    logging.getLogger().setLevel(args.loglevel.upper())
    backupManger = BackupManager(args, logger)
    backupManger.run()


###############################################################################
# MAIN
###############################################################################

if __name__ == '__main__':
    main()
