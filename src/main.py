import click
import os
import re
import logging
import ast
import psutil

# bytes pretty-printing
UNITS_MAPPING = [
    (1 << 50, ' PB'),
    (1 << 40, ' TB'),
    (1 << 30, ' GB'),
    (1 << 20, ' MB'),
    (1 << 10, ' KB'),
    (1, (' byte', ' bytes')),
]


def configure(log_level='INFO'):
    logging.basicConfig(level=eval("logging."+log_level), format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

def check_disk_usage(directory):
    ''' checks the disk usage '''
    hdd = psutil.disk_usage(directory)
    return hdd.free

'''
    For the given path, get the List of all files in the directory tree 
'''
def get_file_list(dirName='.'):
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


@click.command()
@click.option("--directories", help="Directories to scan", required=True)
@click.option("--free", default="10 GB", help="Minimum free space. Accepts huamn readable format e.g 10MB, 10GB, 1TB", required=True)
@click.option("--threshold", default="20 GB", help="Minimum space to be freed")
@click.option("--log_level", default="20 GB", help="Log Level: DEBUG, INFO, WARNING, ERROR")
def disk_space_calc(directories, free, threshold, log_level):
    """ Check free disk space and 
    return a list of files 
    to be moved/deleted from 
    disk to reach a desired 
    threshold of free space. 
    """
    configure(log_level)


    if (directories is None):
        logging.debug("Directory is empty, skipping")
        return False
    
    free_bytes = check_disk_usage(".")

    if (free_bytes > human_read_to_byte(free)):
        logging.debug("There is enugh free space: " + byte_to_human_read(free_bytes))
        return False

    files = []
    for directory in ast.literal_eval(directories):
        files = files + [file for file in get_file_list(directory)]
    
    files.sort(key=os.path.getmtime)

    byte_sum = 0

    files_to_clean = []

    for file in sorted(files, key=os.path.getmtime):
        if (byte_sum > human_read_to_byte(threshold)):
            return files_to_clean
        byte_sum += os.path.getsize(file)
        files_to_clean.append(file)

    logging.debug("Files collected: %s", str(files_to_clean))

    return files_to_clean

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
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    size = size.split()                # divide '1 GB' into ['1', 'GB']
    num, unit = int(size[0]), size[1]
    # index in list of sizes determines power to raise it to
    idx = size_name.index(unit)
    # ** is the "exponent" operator - you can use it instead of math.pow()
    factor = 1024 ** idx
    return num * factor


if __name__ == '__main__':
    configure()
    disk_space_calc()
