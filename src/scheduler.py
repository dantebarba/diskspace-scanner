import main
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

sched = BlockingScheduler()

def do_nothing():
    pass

def configure(cron_expression, task=do_nothing):
    ''' Configures the scheduler given a cron_expression and a task to execute '''
    logging.debug("Configuring scheduler with %s", cron_expression)
    sched.add_job(task, CronTrigger.from_crontab(cron_expression))

def start():
    logging.debug("Starting BlockingScheduler")
    sched.start()
