from setuptools import find_packages, setup
from setuptools.command.install import install

import os
import shutil, errno

def copyall(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise

class CustomInstallCommand(install):
    """Customized setuptools install command - prints a friendly greeting."""
    def run(self):
        print "----------dLimen Installation starting----------"
        current_dir = os.path.dirname(os.path.realpath(__file__))
	print "Copying dir into /usr/local/bin/dlimen"
	copyall(current_dir, '/usr/local/bin/dlimen') 
	print "Copying upstart job into /etc/init/dlimen.conf"
	copyall(current_dir+'/init/dlimen.conf', '/etc/init/.')
	install.run(self)

	print "----------dLimen Installation completed---------"


setup(
    name = 'dLimen',
    version = '0.1',
    author = "kostas",
    packages = find_packages(),
    install_requires = ["pyudev", "configparser", "hurry.filesize"],
    cmdclass={
        'install': CustomInstallCommand,
    }
)
