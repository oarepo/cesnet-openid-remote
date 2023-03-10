# Copyright (C) 2023 CESNET.

import os
from setuptools import find_packages, setup

readme = open('README.md').read()

OAREPO_VERSION = os.environ.get('OAREPO_VERSION', '3.3.0')

packages = find_packages(exclude=['tests'])

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('cesnet_openid_remote', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='cesnet-openid-remote',
    version=version,
    description=__doc__,
    long_description=readme,
    license='MIT',
    author='Juraj Trappl',
    author_email='jtrappl@techlib.cz',
    packages=packages
)