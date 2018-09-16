#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


deps = {
    'beacon_chain': [
        "eth-typing>=1.1.0,<2.0.0",
        "py-ecc==1.4.3",
        "pyblake2==1.1.2",
    ],
    'test': [
        "eth-tester[py-evm]==0.1.0b29",
        "vyper==0.1.0b2",
        "web3==4.3.0",
        "pytest==3.6.1",
        "pytest-mock==1.10.0",
    ],
    'lint': [
        "mypy==0.620",
        "flake8==3.5.0",
    ],
}


deps['dev'] = (
    deps['beacon_chain'] +
    deps['test'] +
    deps['lint']
)

install_requires = deps['beacon_chain']

setup(
    name='beacon_chain',
    version='0.0.1-alpha.1',
    description='',
    url='https://github.com/ethereum/beacon_chain',
    packages=find_packages(
        exclude=[
            "tests",
            "tests.*",
        ]
    ),
    python_requires='==3.6.*',
    py_modules=['beacon_chain', 'ssz'],
    extras_require=deps,
    setup_requires=['setuptools-markdown'],
    long_description_markdown_filename='README.md',
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=install_requires,
)
