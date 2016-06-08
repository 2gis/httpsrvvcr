import unittest

import httpsrv
import requests

from httpsrvvcr.player import tape_from_yaml, Player


server = httpsrv.Server(8080).start()
player = Player(server)


class RealTapePlaybackTest(unittest.TestCase):
    def setUp(self):
        server.reset()

    def test_should_play_real_tape(self):
        with open('tests/tape.yaml', 'r', encoding='utf8') as tape_file:
            tape_text = tape_file.read()
            tape = tape_from_yaml(tape_text)
            player.play(tape)
        res = requests.post('http://localhost:8080/api/users',
                            json={'name': 'John', 'last_name': 'Doe'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json(), {
            'id': 42,
            'name': 'John',
            'last_name': 'Doe'
        })
        res = requests.post('http://localhost:8080/api/users',
                            json={'name': 'Jane', 'last_name': 'Doe'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json(), {
            'id': 43,
            'name': 'Jane',
            'last_name': 'Doe'
        })

    @player.load('tests/tape.yaml')
    def test_should_play_real_tape_from_decorator(self):
        res = requests.post('http://localhost:8080/api/users',
                            json={'name': 'John', 'last_name': 'Doe'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json(), {
            'id': 42,
            'name': 'John',
            'last_name': 'Doe'
        })
        res = requests.post('http://localhost:8080/api/users',
                            json={'name': 'Jane', 'last_name': 'Doe'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json(), {
            'id': 43,
            'name': 'Jane',
            'last_name': 'Doe'
        })

