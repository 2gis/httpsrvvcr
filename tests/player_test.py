import unittest
from unittest.mock import Mock, call

from httpsrvvcr.player import Player, tape_from_yaml


class PlayerTest(unittest.TestCase):
    def setUp(self):
        self.tape = [
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'text': None,
                    'json': {'name': 'John', 'last_name': 'Doe'},
                },
                'response': {
                    'code': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'text': None,
                    'json': {'id': 42, 'name': 'John', 'last_name': 'Doe'},
                }
            },
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'text': None,
                    'json': {'name': 'Jane', 'last_name': 'Doe'},
                },
                'response': {
                    'code': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'text': None,
                    'json': {'id': 43, 'name': 'Jane', 'last_name': 'Doe'},
                }
            },
        ]
        self.rule = Mock()
        self.server = Mock()
        self.server.on = Mock(return_value=self.rule)
        self.player = Player(self.server)

    def test_should_setup_server_for_post_request(self):
        request1 = self.tape[0]['request']
        request2 = self.tape[1]['request']
        self.player.play(self.tape)
        self.server.on.assert_has_calls([
            call('POST', '/api/users', request1['headers'],
                 text=request1['text'], json=request1['json']),
            call('POST', '/api/users', request2['headers'],
                 text=request2['text'], json=request2['json']),
        ])

    def test_should_setup_server_for_post_response(self):
        response1 = self.tape[0]['response']
        response2 = self.tape[1]['response']
        self.player.play(self.tape)
        self.rule.json.assert_has_calls([
            call(response1['json'], response1['code'], response1['headers']),
            call(response2['json'], response2['code'], response2['headers']),
        ])


    def test_should_respond_with_text(self):
        tape = {
            'request': {
                'path': '/api/users',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'text': None,
                'json': {'name': 'John', 'last_name': 'Doe'},
            },
            'response': {
                'code': 200,
                'headers': {'Content-Type': 'text/html'},
                'text': '<h1>Boom</h1>',
                'json': None,
            }
        }
        self.player.play([tape])
        response = tape['response']
        self.rule.text.assert_has_calls([
            call(response['text'], response['code'], response['headers']),
        ])

    def test_should_ignore_transfer_encoding(self):
        tape = {
            'request': {
                'path': '/api/users',
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'Transfer-Encoding': 'chunked',
                },
                'text': None,
                'json': None,
            },
            'response': {
                'code': 200,
                'headers': {'Content-Type': 'text/html'},
                'text': '<h1>Boom</h1>',
                'json': None,
            }
        }
        self.player.play([tape])
        self.server.on.assert_has_calls([
            call('POST', '/api/users', {'Content-Type': 'application/json'},
                 json=None, text=None),
        ])

    def test_should_add_cors_header_to_response(self):
        tape = {
            'request': {
                'path': '/api/users',
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'Transfer-Encoding': 'chunked',
                },
                'text': None,
                'json': None,
            },
            'response': {
                'code': 200,
                'headers': {'Content-Type': 'text/html'},
                'text': '<h1>Boom</h1>',
                'json': None,
            }
        }
        cors_player = Player(self.server, True)
        cors_player.play([tape])
        response = tape['response']
        self.rule.text.assert_has_calls([
            call(response['text'], response['code'], {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*'
            }),
        ])

    def test_should_create_properly_named_decorator(self):
        @self.player.load('foo')
        def some_wrapped():
            pass

        self.assertEqual(some_wrapped.__name__, 'some_wrapped')


class YamlReaderTest(unittest.TestCase):
    def test_should_read_tape_from_yaml_text(self):
        text = '''
        - request:
            path: /api/users
            method: POST
            headers:
              Content-Type: application/json
            text: null
            json:
              name: John
              last_name: Doe
          response:
            code: 200
            headers:
              Content-Type: application/json
            text: null
            json:
              id: 42
              name: John
              last_name: Doe
        '''
        expected = [
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'text': None,
                    'json': {'name': 'John', 'last_name': 'Doe'},
                },
                'response': {
                    'code': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'text': None,
                    'json': {'id': 42, 'name': 'John', 'last_name': 'Doe'},
                }
            },
        ]
        result = tape_from_yaml(text)
        self.assertEqual(expected, result)

