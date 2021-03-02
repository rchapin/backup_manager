import sys
import logging
import argparse
from backupmanager.lib.backupmanager import BackupManager

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

    # Build a standard dict of the CLI args
    args = parser.parse_args()
    return dict(
        configfile=args.configfile,
        loglevel=args.loglevel,
        dryrun=args.dryrun,
        )

def main():
    args = parse_args()
    logging.getLogger().setLevel(args['loglevel'].upper())
    backupManger = BackupManager(args)
    backupManger.run()
    logger.info('Exiting process')

###############################################################################
# MAIN
###############################################################################

if __name__ == '__main__':
    main()
