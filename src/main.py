import click
import os
import re
import logging
import ast
import psutil
import sys
import api
import scheduler

# bytes pretty-printing
UNITS_MAPPING = [
    (1 << 50, 'P'),
    (1 << 40, 'T'),
    (1 << 30, 'G'),
    (1 << 20, 'M'),
    (1 << 10, 'K'),
    (1, ('B', ' bytes')),
]


def configure(log_level='INFO'):
    root = logging.getLogger()
    root.setLevel(eval("logging."+log_level))
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(eval("logging."+log_level))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def set_cron_lock():
    ''' sets a lock to prevent more executions while doing a calculation '''
    pass


def release_cron_lock():
    ''' release the cron lock '''
    pass


def check_disk_usage(directory):
    ''' checks the disk usage '''
    hdd = psutil.disk_usage(directory)
    return hdd.free


def get_file_list(dirName='.'):
    '''
        For the given path, get the List of all files in the directory tree
    '''
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + get_file_list(fullPath)
        else:
            allFiles.append(fullPath)

    return allFiles


def calc_demanded_space(free_bytes, free, threshold):
    return free + threshold - free_bytes


def read_directories(directories=[]):
    files = []
    for directory in directories:
        files = files + [file for file in get_file_list(directory)]
    return files


def collect_files_to_clean(files, free_space_needed):
    byte_sum = 0
    files_to_clean = []

    for file in sorted(files, key=os.path.getmtime):

        if (byte_sum >= free_space_needed):
            logging.debug("Files collected: %s", str(files_to_clean))
            return files_to_clean

        byte_sum += os.path.getsize(file)
        files_to_clean.append(file)

    logging.debug("Files collected: %s", str(files_to_clean))

    logging.warning("Not enough files can be collected to reach threshold. Total collected %s. Required %s",
                    byte_to_human_read(byte_sum), byte_to_human_read(free_space_needed))

    return files_to_clean


@click.command()
@click.option("--directories", help="Directories to scan", required=True)
@click.option("--free", default="10G", help="Minimum free space to trigger cleanup. Accepts huamn readable format e.g 10M, 10G, 1T", required=True)
@click.option("--threshold", default="20G", help="Minimum space to be freed")
@click.option("--log_level", default="INFO", help="Log Level: DEBUG, INFO, WARNING, ERROR")
@click.option("--remote_path_mapping", default="{}", help="Remote paths mapping in dict structure")
@click.option("--rclone_url", help="Remote Rclone RCD Url. e.g http://yourrcloneurl:5573", required=True)
@click.option("--source_remote", default="/", help="The remote source drive name if any.")
@click.option("--dest_remote", default="/", help="The remote destination drive name if any. Usually it's just '/'")
@click.option("--auth_user", default="", help="Auth username")
@click.option("--auth_password", default="", help="Auth password")
@click.option("--dry_run", default='True', help="Dry Run")
@click.option("--scheduled", default=None, help="Enable scheduled execution. Parameter should be a crontab expression")
def disk_space_calc(directories, free, threshold, log_level, remote_path_mapping, rclone_url, source_remote, dest_remote, auth_user, auth_password, dry_run, scheduled):
    """ Check free disk space and 
    return a list of files 
    to be moved/deleted from 
    disk to reach a desired 
    threshold of free space. 
    """
    configure(log_level)

    if not scheduled:
        logging.debug("One time execution is enabled.")
        do_calculation_and_move(directories, free, threshold, remote_path_mapping,
                                rclone_url, source_remote, dest_remote, auth_user, auth_password, dry_run)

    if scheduled:
        logging.debug("Scheduler is enabled. Task will be scheduled to run at %s", scheduled)
        scheduler.configure(scheduled, lambda:         do_calculation_and_move(directories, free, threshold, remote_path_mapping,
                                                                               rclone_url, source_remote, dest_remote, auth_user, auth_password, dry_run))
        scheduler.start()


def do_calculation_and_move(directories, free, threshold, remote_path_mapping, rclone_url, source_remote, dest_remote, auth_user, auth_password, dry_run):
    if (directories is None):
        logging.debug("Directory is empty, skipping")
        return False

    logging.debug("Starting directory clean --- Filesystem check")
    logging.debug("Free space is set at: %s", free)
    logging.debug("Threshold is set at: %s", threshold)

    free_bytes = check_disk_usage(".")

    logging.debug("Free space available is: %s",
                  byte_to_human_read(free_bytes))

    if (free_bytes > human_read_to_byte(free)):
        logging.debug("There is enugh free space: " +
                      byte_to_human_read(free_bytes))
        return False

    logging.debug("Reading directories: %s", str(directories))

    files = read_directories(ast.literal_eval(directories))

    files.sort(key=os.path.getmtime)

    logging.debug("Collecting files from available set: %s", str(files))

    free_space_needed = calc_demanded_space(
        free_bytes, human_read_to_byte(free), human_read_to_byte(threshold))

    logging.debug("Space that needs to be freed: %s",
                  byte_to_human_read(free_space_needed))

    files_collected = collect_files_to_clean(files, free_space_needed)

    api.fire_api_move(files=files_collected, url=rclone_url, remote_path_mapping=ast.literal_eval(
        remote_path_mapping), remote_source=source_remote, remote_dest=dest_remote, username=auth_user, password=auth_password, dry_run=ast.literal_eval(dry_run))


def byte_to_human_read(bytes, units=UNITS_MAPPING):
    """Get human-readable file sizes.
    simplified version of https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = int(bytes / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix


def human_read_to_byte(size):
    size_name = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
    num, unit = int(size[0:-1]), size[-1]
    # index in list of sizes determines power to raise it to
    idx = size_name.index(unit)
    # ** is the "exponent" operator - you can use it instead of math.pow()
    factor = 1024 ** idx
    return num * factor


if __name__ == '__main__':
    disk_space_calc()
