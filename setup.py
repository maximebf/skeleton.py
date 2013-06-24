#!/usr/bin/env python

from distutils.core import setup

setup(name='skeleton',
      version='1.0',
      description='Create directory structures and files out of a skeleton template',
      author='Maxime Bouroumeau-Fuseau',
      author_email='maxime.bouroumeau@gmail.com',
      py_modules=['skeleton'],
      scripts=['bin/skeleton']
     )
