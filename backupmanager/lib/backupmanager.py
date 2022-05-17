import logging
import multiprocessing
import os
import signal
import sys
from backupmanager.lib.utils import Utils
from backupmanager.lib.rsync import Rsync
from apscheduler import events
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from invoke import run

logging.basicConfig(
    format="%(asctime)s,%(levelname)s,%(module)s,%(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

PID_FILE_NAME = "pid"
ENV_VAR_PREFIX = "BACKUPMGRINTTEST"


class BackupManager(object):
    def __init__(self, args):
        logging.getLogger().setLevel(args["loglevel"].upper())
        self.configfile = args["configfile"]
        self.dryrun = args["dryrun"]

        self.configs = Utils.load_configs(self.configfile)
        # TODO: validate configs

        if not Utils.write_pid(
            logger=logger, configs=self.configs, pid_file_name=PID_FILE_NAME
        ):
            logger.info("Shutting down")
            return

        self.rsync_impl = self.configs["rsync_impl"]
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self.event_listener)
        self.running = False
        self.is_shutdown = False
        self.cron_schedule = self.configs["cron_schedule"]
        self.process = None

        env_vars = Utils.get_env_vars(ENV_VAR_PREFIX)
        runonce_env_var_key = f"{ENV_VAR_PREFIX}_RUNONCE"
        if runonce_env_var_key in env_vars:
            self.runonce = True if env_vars[runonce_env_var_key] is "1" else False
        else:
            self.runonce = False

    def event_listener(self, event):
        if event.code == events.EVENT_JOB_ADDED:
            for job in self.scheduler.get_jobs():
                if event.code != events.EVENT_JOB_EXECUTED:
                    logger.info(
                        f"Job id={job.id}, scheduled for next run at {job.next_run_time}"
                    )

        if self.runonce and event.code == events.EVENT_JOB_EXECUTED:
            if self.scheduler.running:
                logger.info("Shutting down scheduler")
                job = self.scheduler.get_job("runonce")
                logger.info(f"job={job}")
                try:
                    self.scheduler.shutdown(wait=False)
                except Exception as e:
                    logger.info(f"Caught exception shutting down the scheduler; e={e}")

    def run(self):
        # # Register for the SIGTERM signal so that we can cleanly shutdown
        # signal.signal(signal.SIGTERM, self.signal_handler)

        self.scheduler.start()
        if self.runonce:
            self.schedule_runonce_job()
        else:
            self.schedule_cron_job()

        while self.scheduler.running:
            self.scheduler._thread.join(0.1)
        logger.info("BackupManager exiting run")

    def exec_job(self):
        logger.info("Starting exec_job....")
        if self.running:
            logger.warning(f"Unable to schedule multiple...")
            return

        self.running = True

        """
        """
        self.process = multiprocessing.Process(target=self.exec_process)
        self.process.start()
        self.process.join()

        #     .start()
        #     time.sleep(10)
        #     p.terminate()
        #     p.join()

        self.running = False
        logger.info("Finishing exec_job....")

    def exec_process(self):
        # Iterate over all of the sync_jobs.
        for job in self.configs["jobs"]:
            logger.info(f"Executing job={job}")

            """
            We run the rsync command in a separate process altogether so that
            we can kill it if need be.  Otherwise, we block on it.
            """
            rsync = Rsync()

            # Some OS command to simulate a long running process
            run('while true; do echo "sleep"; sleep 2; done')
            # '''
            # First, check to see if there is a 'blocks_on' key defined for this job.
            # If so, ensure that there is no pid file with an running process on the
            # defined host.
            # '''
            # if 'blocks_on' in sync_job:
            # blocks_on = sync_job['blocks_on']
            # logger.info(f'Validating blocks_on={blocks_on}')
            # pass

        pass

    def schedule_runonce_job(self):
        if not self.running:
            logger.info(f"Scheduling a runonce job")
            self.scheduler.add_job(max_instances=1, id="runonce", func=self.exec_job)

    def schedule_cron_job(self):
        logger.info(f"Scheduling cron job with schedule={self.cron_schedule}")
        self.scheduler.add_job(
            func=self.exec_job, trigger=CronTrigger.from_crontab(self.cron_schedule)
        )

    def shutdown(self):
        logger.info("Shutting down ....")
        # Kill any running process if one exists
        if self.process is not None:
            if self.process.is_alive():
                self.process.terminate()
                # FIXME: make the timeout configurable
                self.process.join(5)

        self.scheduler.shutdown(wait=False)
        self.is_shutdown = True

    # def signal_handler(self, signal, frame):
    # logger(f'Handling signal={signal}, frame={frame}')
    # self.scheduler.shutdown(wait=True)
