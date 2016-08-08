from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))
long_description = None
version = None

# Get the long description from the README file
with open(path.join(here, 'Readme.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, '.version'), encoding='utf-8') as f:
    version = f.read()

setup(
    name='httpsrvvcr',
    version=version,
    description='VCR recording proxy-server for usage with httpsrv',
    long_description=long_description,
    url='https://github.com/2gis/httpsrvvcr',
    author='2GIS',
    author_email='a.nyrkov@2gis.ru',
    license='MIT',
    packages=['httpsrvvcr'],

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='api http mock testing vcr',
    install_requires=['tornado', 'pyyaml', 'httpsrv'],
    extras_require={
        'test': ['requests'],
    },
)
