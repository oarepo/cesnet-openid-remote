# Copyright (C) 2023 CESNET.

import os
from setuptools import find_packages, setup

readme = open('README.md').read()

packages = find_packages(exclude=['tests'])

setup(
    name='cesnet-openid-remote',
    version='0.0.1',
    description=__doc__,
    long_description=readme,
    license='MIT',
    author='Juraj Trappl',
    author_email='jtrappl@techlib.cz',
    packages=packages
)