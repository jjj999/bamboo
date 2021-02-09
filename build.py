#!Python3

"""Script for build the package.

This script has to be executed with the super user authority,
so the package would be included into site-packages of 
the python the inner system uses.
"""

import subprocess

from setup import setup


def before_install():
    subprocess.run(["apt-get", "install", "libpq-dev"])


if __name__ == "__main__":
    before_install()
    setup()
