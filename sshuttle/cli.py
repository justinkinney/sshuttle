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


def cook_rcfile(opts, data):
    """
    Join elements of passed list and return a URI encoded string

    Args:
      data (list): list of lines

    Returns:
      data (str): URI encoded string
    """
    data = SSHUTTLE_EOL.join(data)
    encoded = base64.b64encode(data.encode('utf-8')).decode('utf-8')
    if opts.verbose:
        print(f"encoded rc file: {encoded}")
    return encoded


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
        "familiar home on remote systems"
    )
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser


def default_rcfile(opts):
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
    lines = [line.rstrip() for line in default.split("\n")]
    lines.insert(0, "TMPDIR=/tmp/sshuttle.{}".format(SSHUTTLEID))
    return lines


def read_rcfile(opts, rcfile):
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


def get_user_rcfiles(opts):
    """
    Search default paths for rcfiles, read them, and return a list of lines
    Note: contents of .sshuttlerc.d are read first since they are more likely
    to contain functions

    Args:
        None

    Returns:
        script (list): aggregated list of lines from all scripts
    """
    search_files = []
    search_files.append(os.path.join(os.environ["HOME"], ".sshuttlerc.d"))
    search_files.append(os.path.join(os.environ["HOME"], ".sshuttlerc"))

    script = []
    for rcfile in search_files:
        if os.path.isfile(rcfile):
            script += read_rcfile(opts, rcfile)
        if os.path.isdir(rcfile):
            for rcdfile in os.listdir(rcfile):
                script += read_rcfile(opts, os.path.join(rcfile, rcdfile))
    return script


def get_inject_string_base64(opts, command_script):
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
        eol=SSHUTTLE_EOL,
    )


def connect(opts, target_host, ssh_options, command_script):
    """
    Connect to the host and inject our commands

    Args:

    Returns:
        None
    """
    cmd_line = ""
    cmd_line += get_inject_string_base64(opts, command_script)
    cmd_line += "; /usr/bin/ssh -t"

    for option in ssh_options:
        cmd_line += " {}".format(option)

    cmd_line += """ {target_host} \"$INJECT;
        exec /bin/bash --rcfile {tmpdir}/rc\"""".format(
        target_host=target_host, tmpdir="/tmp/sshuttle.{}".format(SSHUTTLEID)
    )
    os.system(cmd_line)


def main(opts, args):
    """
    Build the injection string and connect to the host
    """
    target_host = args.pop(0)

    if opts.verbose:
        print(f"target host: {target_host}")

    if len(args) > 0:
        ssh_args = args
    else:
        ssh_args = ""

    if opts.verbose:
        print(f"ssh arguments: {ssh_args}")

    rcfile = default_rcfile(opts)
    rcfile += get_user_rcfiles(opts)
    inject_string = cook_rcfile(opts, rcfile)
    connect(opts, target_host, ssh_args, inject_string)


def cli():
    parser = get_parser()
    opts, args = parser.parse_known_args()

    if opts.verbose:
        print(f"options: {opts}")
        print(f"arguments: {args}")

    if not len(args) > 0:
        parser.print_help()
        sys.exit(1)

    sys.exit(main(opts, args))


if __name__ == "__main__":
    cli()
