#!/usr/bin/env python

from distutils.core import setup

setup(name='matplotlib-sixel',
      version='0.1',
      description='Matplotlib backend for showing sixel graphics',
      requires=['libsixel-python'],
      author='Markus Gräb',
      author_email='markus.graeb@gmail.com',
      url='https://github.com/koppa/matplotlib-sixel',
      packages=['matplotlib-sixel'])
