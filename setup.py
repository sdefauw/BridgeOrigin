#!/usr/bin/env python
# coding: utf-8

__author__ = "Sebastien De Fauw"

from setuptools import setup, find_packages

setup(
    name="Bridge Origin",
    version="0.1.0",
    description='Bridge Origin is a tool to unify network traces and log files.',

    # simple to run
    entry_points={
        'console_scripts': [
            'brorig = brorig.main:setup',
            ],
        },

    author='Sebastien De Fauw',
    author_email="sdefauw@gmail.com",

    packages=find_packages(exclude=('tests', 'docs')),

    include_package_data=True, #include data from MANIFEST.in

    download_url = (""),

    install_requires=[
        'tornado>=4.0.0',
        'paramiko>=1.14.0',
        'pymysql>=0.6.6'
    ],


)