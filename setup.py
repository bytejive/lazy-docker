#!/usr/bin/env python

from distutils.core import setup

setup(
    name='lazy_docker',
    version='1.0',
    description='A Docker and Docker Machine CLI wrapper designed to greatly '
                'simplify and automate large stack deployments.',
    author='ByteJive',
    author_email='johnstarich@johnstarich.com',
    url='https://github.com/bytejive/lazy-docker',
    packages=[
    ],
    extras_require={
        'test': [
            'nose',
            'pep8'
        ]
    },
)
