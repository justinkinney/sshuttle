#!/usr/bin/env python
"""
sshuttle allows you to maintain a familiar environment with you when you
connect to new hosts.

It does this by injecting a customizable bashrc during your ssh session setup.
"""

import argparse
import base64
import os
import random
import sys

SSHUTTLE_EOL = "_EOL"
SSHUTTLEID = random.randint(10000, 99999)


def cook_rcfile(data):
    """
    Join elements of passed list and return a URI encoded string

    Args:
      data (list): list of lines

    Returns:
      data (str): URI encoded string
    """
    data = SSHUTTLE_EOL.join(data)
    return base64.b64encode(data)


def get_parser():
    """
    Generate a argparse.ArgumentParser object

    Args:
        None

    Returns:
        argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        usage="%(prog)s [ssh-opts] <host>",
        description="%(prog)s takes advantage of bash to give you a "
        "familiar home on remote systems")
    return parser


def default_rcfile():
    """
    Return a simple default rcfile

    Args:
      none

    Returns:
      data (list): default rc file contents
    """
    default = """PS1="\\[\\e[00;31m\\]\\u\\[\\e[0m\\]\\[\\e[00;37m\\]@\\[\\e[0m\\]\\[\\e[00;36m\\]\\h\\[\\e[0m\\]\\[\\e[00;37m\\]:\\w \\[\\e[0m\\]"
cleaner () {
    echo "cleaning up sshuttle remnants!"
    rm -rf $TMPDIR;
}
trap cleaner SIGINT SIGTERM EXIT
"""
    lines = [line.rstrip() for line in default.split('\n')]
    lines.insert(0, "TMPDIR=/tmp/sshuttle.{}".format(SSHUTTLEID))
    return lines


def read_rcfile(rcfile):
    """
    Read the file specified by the passed filename and return a list of
    lines with newlines stripped

    Args:
      rcfile (str): a path to the rc file to read

    Returns:
      data (list): list of lines with newlines stripped
    """
    script = ["# following sourced from {}".format(rcfile)]
    with open(rcfile) as f:
        script += f.readlines()
    return [line.rstrip() for line in script]


def get_user_rcfiles():
    """
    Search default paths for rcfiles, read them, and return a list of lines
    Note: contents of .sshuttlerc.d are read first since they are more likely to
    contain functions

    Args:
        None

    Returns:
        script (list): aggregated list of lines from all scripts
    """
    search_files = []
    search_files.append(os.path.join(os.environ['HOME'], '.sshuttlerc.d'))
    search_files.append(os.path.join(os.environ['HOME'], '.sshuttlerc'))

    script = []
    for rcfile in search_files:
        if os.path.isfile(rcfile):
            script += read_rcfile(rcfile)
        if os.path.isdir(rcfile):
            for rcdfile in os.listdir(rcfile):
                script += read_rcfile(os.path.join(rcfile, rcdfile))
    return script


def get_inject_string_base64(command_script):
    """
    Return a base64 encoded string which includes shell injection

    Args:

    Returns:
        script (string)
    """
    return """INJECT=\"mkdir {tmpdir};
              echo \\$(echo '{cmd}' |
              base64 -di -) |
              sed 's/{eol}/\\n/g' >{tmpdir}/rc\"""".format(
        tmpdir="/tmp/sshuttle.{}".format(SSHUTTLEID),
        cmd=command_script,
        eol=SSHUTTLE_EOL)


def connect(target_host, ssh_options, command_script):
    """
    Connect to the host and inject our commands

    Args:

    Returns:
        None
    """
    cmd_line = ''
    cmd_line += get_inject_string_base64(command_script)
    cmd_line += "; /usr/bin/ssh -t"

    for option in ssh_options:
        cmd_line += " {}".format(option)

    cmd_line += """ {target_host} \"$INJECT;
        exec /bin/bash --rcfile {tmpdir}/rc\"""".format(
        target_host=target_host,
        tmpdir="/tmp/sshuttle.{}".format(SSHUTTLEID))
    os.system(cmd_line)


def main(args):
    """
    Build the injection string and connect to the host
    """
    target_host = args[1].pop()
    if len(args[1]) > 0:
        ssh_options = args[1]
    else:
        ssh_options = ""

    rcfile = default_rcfile()
    rcfile += get_user_rcfiles()
    inject_string = cook_rcfile(rcfile)
    connect(target_host, ssh_options, inject_string)


def cli():
    parser = get_parser()
    args = parser.parse_known_args()

    if not len(args[1]) > 0:
        parser.print_help()
        sys.exit(1)

    sys.exit(main(args))


if __name__ == "__main__":
    cli()
