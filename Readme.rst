Httpsrv VCR
===========

Library for recording http requests into yaml format that can be
further understood by httpsrv_ as a server fixture

Installation
------------

Package can be obtained from PyPi

::

    pip install httpsrvvcr


Usage
-----

::

    python -m httpsrvvcr.recorder 8080 http://some-api-url.com/api > tape.yaml


.. _httpsrv: https://github.com/nyrkovalex/httpsrv
