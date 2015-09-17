from setuptools import find_packages, setup


setup(
    name = 'socketserver',
    version = '0.1',
    author = "mike, kostas, adam",
    packages = find_packages(),
    install_requires = ["pyudev", "configparser", "hurry.filesize"])
