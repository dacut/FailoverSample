#!/usr/bin/env python
from __future__ import absolute_import, print_function
from setuptools import setup

setup(name="FailoverSample",
      version="0.1.0",
      py_modules=["failover"],
      entry_points={
          "console_scripts": [
              "failover-server=failover:start_failover_server",
          ]
      },
      test_suite="tests",
      install_requires=["boto>=2.0", "six>=1.8"],

      # PyPI information
      author="David Cuthbert",
      author_email="dacut@kanga.org",
      description="Sample failover scripts for aggregating health checks",
      license="BSD",
      url="https://github.com/dacut/FailoverSample",
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords = ['testing', 'failover', 'healthcheck'],
      zip_safe=False,
)

