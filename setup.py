#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


long_description = open('README.rst').read()

setup(
    name='subdivx-download',
    version='0.4',
    description='A program to download the best matching subtitle from subdivx.com',
    long_description=long_description,
    author=u"Martin Gaitan, based on a Michel Peterson's work",
    author_email='gaitan@gmail.com',
    url='https://github.com/mgaitan/subdivx-download',
    packages=['subdivx',],
    license='GNU GENERAL PUBLIC LICENCE v3.0',
    install_requires=['BeautifulSoup4', 'tvnamer'],
    entry_points={
        'console_scripts': ['subdivx-download=subdivx.smarter:main'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: Spanish',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ]
)
