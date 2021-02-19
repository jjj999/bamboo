#! python3
"""
Update local site-packages.

This script make your debug faster.

"""

from os.path import join, expanduser, abspath, exists
import shutil


name_pkg = "dermserver"
path = abspath(join(expanduser("~"),    # TODO Edit path of the package 
                    name_pkg, 
                    name_pkg))
name_env = "dermserver-"                # TODO Edit your env name

version_python = "3.7"
path_site = join(expanduser("~"),
                 ".local",
                 "share",
                 "virtualenvs",
                 name_env,
                 "lib",
                 "python" + version_python, 
                 "site-packages", 
                 name_pkg)


def main():
    if exists(path_site):
        shutil.rmtree(path_site)

    shutil.copytree(path, path_site)
    
if __name__ == "__main__":
    main()
