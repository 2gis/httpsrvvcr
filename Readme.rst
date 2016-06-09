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

Basic usage looks like following::

    python -m httpsrvvcr.recorder 8080 http://some-api-url.com/api > tape.yaml


It is possible to skip headers recording with ``--no-headers`` flag::

    python -m httpsrvvcr.recorder 8080 http://some-api-url.com/api --no-headers > tape.yaml


After vcr tape is recorded one can use ``httpsrvvcr.player`` module::

    import unittest

    from httpsrv import Server
    from httpsrvvcr.player import Player

    server = Server(8080).start()
    player = Player(server)

    class MyTestCase(unittest.TestCase):
        def setUp(self):
            server.reset()

        @player.load('path/to/tape.yaml')
        def test_should_do_something(self):
            pass


.. _httpsrv: https://github.com/nyrkovalex/httpsrv


Documentation
-------------

http://httpsrvvcr.readthedocs.io
