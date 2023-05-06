#!/usr/bin/env python

from setuptools import setup
from os import path

packages = [
    'cc_monitoring',
]

requires = ['requests']
setup_requires = ['setuptools_scm']

extras_require = {
    'test': ['pytest', 'pytest-cov', 'pytest-sugar'],
    'dev': ['pylint', 'flake8'],
}

scripts = []

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    description = f.read()

setup(
    name='cc-monitoring',
    use_scm_version=True,
    description='Tools to monitor Common Crawl infrastructure',
    long_description=description,
    long_description_content_type='text/markdown',
    author='Greg Lindahl',
    author_email='greg@commoncrawl.org',
    url='https://github.com/commoncrawl/cc-monitoring',
    packages=packages,
    python_requires=">=3.6",
    extras_require=extras_require,
    include_package_data=True,
    setup_requires=setup_requires,
    install_requires=requires,
    entry_points='''
        [console_scripts]
        ccm = cc_monitoring.cli:main
    ''',
    scripts=scripts,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        'Programming Language :: Python',
        #'Programming Language :: Python :: 3.5',  # setuptools_scm now has f-strings
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
