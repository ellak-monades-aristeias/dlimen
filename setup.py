from setuptools import find_packages, setup
import distutils.cmd 
import distutils.log
import os
import shutil, errno

def copyall(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

class CustomInstallCommand(distutils.cmd.Command):
    """Custom dLimen Installer"""

    description = "dLimen installer for the upstart job"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.announce("----------dLimen Installation starting----------",
        level=distutils.log.INFO)
        current_dir = os.path.dirname(os.path.realpath(__file__))
        print "Copying dir into /usr/local/bin/dlimen"
        copyall(current_dir, '/usr/local/bin/dlimen')
        print "Copying upstart job into /etc/init/dlimen.conf"
        copyall(current_dir+'/init/dlimen.conf', '/etc/init/.')
        print "----------dLimen Installation completed---------"

setup(
    cmdclass={
        'dlimen': CustomInstallCommand,
    },
    name = 'dLimen',
    version = '0.1',
    author = "Kostas Giotis",
    packages = find_packages(),
    install_requires = ["pyudev", "configparser", "hurry.filesize"]
)
