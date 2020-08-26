import requests
import logging
import re
import base64


def ping_remote_rclone(remote_url):
    headers = {'Content-Type': 'application/json'}
    r = requests.request('POST', remote_url + "/rc/noop", headers=headers)
    return r.status_code == 200


def rclone_options_config(remote_url, auth, dry_run):

    logging.debug("""Execute parameters: 
    url: %s
    auth: %s""",
    remote_url, auth.decode("utf-8"))

    options = {
        "main" : {
            "DryRun" : dry_run,
            "DeleteEmptySrcDirs" : True
        }
    }
    headers = {'Content-Type': 'application/json',
            "Authorization" : "Basic " + auth.decode("utf-8")}
    r = requests.request('POST', remote_url + "/options/set", headers=headers, json=options)
    r.raise_for_status()

def execute_command(remote_url, command='movefile', srcFs='/', srcRemote='', dstFs='/', dstRemote='', auth='', asyncron=False):

    logging.debug("""Execute parameters: 
    url: %s
    command: %s
    srcFs: %s
    srcRemote: %s
    dstFs: %s
    dstRemote: %s
    auth: %s
    """, remote_url, command, srcFs, srcRemote, dstFs, dstRemote, auth)

    if (remote_url is None or command is None or srcFs is None or srcRemote is None or dstFs is None or dstRemote is None):
        logging.error("Configuration error: Parameters are null")
        return False

    headers = {'Content-Type': 'application/json',
               "Authorization": "Basic " + auth.decode("utf-8")}

    payload = {
	"srcFs": srcFs,
	"srcRemote":  srcRemote,
	"dstFs": dstFs,
	"dstRemote": dstRemote
    }

    r = requests.request('POST', remote_url + "/operations/" +
                     command, headers=headers, json=payload)
    r.raise_for_status()
    return True


def replace_remote_path_mapping(location, remote_path_mapping={}):
    for mapping in remote_path_mapping.keys():
        m = re.search(mapping, location)
        if m:
            return location.replace(m.group(0), remote_path_mapping[mapping])

    return location


def add_ending_separator(drive):
    return drive + \
        ":" if drive and (drive[-1] != ":") and (drive != '/') else drive


def fire_api_move(url, remote_path_mapping, remote_source, remote_dest, username, password, dry_run, files=[]):
    if not url:
        logging.error("No url is set. Skipping move.")
        return False

    remote_source = add_ending_separator(remote_source)

    remote_dest = add_ending_separator(remote_dest)

    auth = username + ":" + password

    b64auth = base64.b64encode(bytes(auth, "utf-8"))

    rclone_options_config(url, auth=b64auth, dry_run=dry_run)

    for file in files:
        execute_command(url, 'movefile', remote_source, replace_remote_path_mapping(
            file, remote_path_mapping), remote_dest, file, auth=b64auth)
