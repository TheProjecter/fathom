#!/usr/bin/python3
#coding=utf-8

from distutils.core import setup

setup(name='fathom', version='0.2.0a1', packages=['fathom'], 
      scripts=['tools/fathom2django.py', 'tools/fathom2graphviz.py'],
      author="Filip Gruszczyński", author_email="gruszczy@gmail.com",
      description="database inspection library",
      url='http://code.google.com/p/fathom',
      classifiers = ["Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        ])
