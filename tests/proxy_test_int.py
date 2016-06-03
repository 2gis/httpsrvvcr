import unittest
import httpsrv
from httpsrvvcr import recorder
import requests
import time

from threading import Thread

SERVER_ADDRESS = 'http://localhost:8888'
PROXY_ADDRESS = 'http://localhost:8889'

class IntegrationalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = httpsrv.Server(8888).start()
        def run_proxy():
            recorder.run(8889, SERVER_ADDRESS)
        cls.proxy_thread = Thread(target=run_proxy)
        cls.proxy_thread.start()
        # wait for recorder to start
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        recorder.stop()
        cls.proxy_thread.join()

    def setUp(self):
        IntegrationalTest.server.reset()

    def test_should_proxy_get_request(self):
        IntegrationalTest.server.on('GET', '/').text('Hello')
        res = requests.get(PROXY_ADDRESS)
        self.assertEqual(res.text, 'Hello')

    def test_should_proxy_post_request(self):
        IntegrationalTest.server.on('POST', '/', text='Foo').text('Hello')
        res = requests.post(PROXY_ADDRESS, data='Foo')
        self.assertEqual(res.text, 'Hello')

    def test_should_proxy_path(self):
        IntegrationalTest.server.on('GET', '/hi').text('Hello')
        res = requests.get(PROXY_ADDRESS + '/hi')
        self.assertEqual(res.text, 'Hello')

    def test_should_proxy_path_with_args(self):
        IntegrationalTest.server.on('GET', '/hi?name=Dude').text('Hello')
        res = requests.get(PROXY_ADDRESS + '/hi?name=Dude')
        self.assertEqual(res.text, 'Hello')

    def test_should_proxy_errorous_code(self):
        IntegrationalTest.server.on('GET', '/').text('Goodbye', status=500)
        res = requests.get(PROXY_ADDRESS + '/')
        self.assertEqual(res.text, 'Goodbye')

