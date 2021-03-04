import sys
import logging
import argparse
import signal
import os
from backupmanager.lib.backupmanager import BackupManager

# For the time-being, we are just logging to the console
logging.basicConfig(
    format='%(asctime)s,%(levelname)s,%(module)s,%(message)s',
    level=logging.INFO,
    stream=sys.stdout)

logger = logging.getLogger(__name__)
backupmanager = None

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

def signal_handler(signal_number, _frame):
    logger.info(f'Caught signal_number={signal_number}')

    if signal_number == signal.SIGHUP:
        pass
        backupmanager.schedule_runonce_job()
    else:
        backupmanager.shutdown()

def main():
    # Register signal handlers to properly shutdown the application.
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    args = parse_args()
    logging.getLogger().setLevel(args['loglevel'].upper())
    try:
        global backupmanager
        backupmanager = BackupManager(args)
        backupmanager.run()
    except KeyboardInterrupt:
        '''
        Catch CTRL+C interrupts so that we can cleanly shutdown; issuing our
        own kill signal to the application.
        '''
        our_pid = os.getpid()
        logger.info(f'Caught KeyboardInterrupt, issuing SIGTERM to our_pid={our_pid}')
        os.kill(our_pid, signal.SIGTERM)
    except Exception as e:
        # Dump the entire stack trace as we do not expect this case.
        logger.exeption(e)

    logger.info('Exiting process')

###############################################################################
# MAIN
###############################################################################

if __name__ == '__main__':
    main()
