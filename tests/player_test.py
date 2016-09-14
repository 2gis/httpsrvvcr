import unittest
from unittest.mock import Mock, call

from httpsrvvcr.player import Player, tape_from_yaml


class PlayerTest(unittest.TestCase):
    def setUp(self):
        self.rule = Mock()
        self.server = Mock()
        self.server.on_json = Mock(return_value=self.rule)
        self.server.on_text = Mock(return_value=self.rule)
        self.server.on_any = Mock(return_value=self.rule)
        self.player = Player(self.server)


class JsonRequestsTest(PlayerTest):
    def setUp(self):
        super().setUp()
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

    def test_should_setup_server_for_json_request(self):
        request1 = self.tape[0]['request']
        request2 = self.tape[1]['request']
        self.player.play(self.tape)
        self.server.on_json.assert_has_calls([
            call('POST', '/api/users', request1['json'], request1['headers']),
            call('POST', '/api/users', request2['json'], request2['headers']),
        ])


class TextRequestTest(PlayerTest):
    def setUp(self):
        super().setUp()
        self.tape = [
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': { 'Content-Type': 'text/plain' },
                    'text': 'Dude',
                    'json': None,
                },
                'response': {
                    'code': 200,
                    'headers': { 'Content-Type': 'text/plain' },
                    'text': 'Lebowski',
                    'json': None,
                }
            }
        ]

    def test_should_setup_server_for_text_request(self):
        request = self.tape[0]['request']
        self.player.play(self.tape)
        self.server.on_text.assert_called_with(
            request['method'], request['path'], request['text'], request['headers'])


class FormRequestTest(PlayerTest):
    def setUp(self):
        super().setUp()
        self.tape = [
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': {'Content-Type': 'text/plain'},
                    'text': None,
                    'json': None,
                    'form': {'dude': 'Lebowski'}
                },
                'response': {
                    'code': 200,
                    'headers': {'Content-Type': 'text/plain'},
                    'text': 'Bowling',
                    'json': None,
                }
            }
        ]

    def test_should_setup_server_for_form_request(self):
        request = self.tape[0]['request']
        self.player.play(self.tape)
        self.server.on_form.assert_called_with(
            request['method'], request['path'], request['form'], request['headers'])


class MultipartUploadTest(PlayerTest):
    def setUp(self):
        super().setUp()
        self.tape = [
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': { 'Content-Type': 'text/plain' },
                    'files': {
                        'bowlers': {
                            'dude': b'Lebowski',
                            'walter': b'Sobchak'
                        }
                    },
                    'text': None,
                    'json': None,
                },
                'response': {
                    'code': 200,
                    'headers': { 'Content-Type': 'text/plain' },
                    'text': 'Strike!',
                    'json': None,
                }
            }
        ]

    def test_should_setup_file_upload_request(self):
        request = self.tape[0]['request']
        self.player.play(self.tape)
        self.server.on_files.assert_called_with(
            request['method'], request['path'], request['files'], None, request['headers'])

    def test_should_include_form_fields(self):
        request = self.tape[0]['request']
        request['form'] = {
            'maude': 'Lebowski'
        }
        self.player.play(self.tape)
        self.server.on_files.assert_called_with(
            request['method'], request['path'], request['files'], request['form'], request['headers'])


class AnyRequestTest(PlayerTest):
    def setUp(self):
        super().setUp()
        self.tape = [
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': { 'Content-Type': 'text/plain' },
                    'text': None,
                    'json': None,
                },
                'response': {
                    'code': 200,
                    'headers': { 'Content-Type': 'text/plain' },
                    'text': 'Lebowski',
                    'json': None,
                }
            }
        ]

    def test_should_setup_server_for_text_request(self):
        request = self.tape[0]['request']
        self.player.play(self.tape)
        self.server.on_any.assert_called_with(
            request['method'], request['path'], request['headers'])

    def test_should_handle_missing_fields(self):
        request = {
            'path': '/api/users',
            'method': 'POST',
        }
        self.tape[0]['request'] = request
        self.player.play(self.tape)
        self.server.on_any.assert_called_with(
            request['method'], request['path'], None)


class JsonResponseTest(PlayerTest):
    def setUp(self):
        super().setUp()
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
            }
        ]

    def test_should_setup_server_for_json_response(self):
        response = self.tape[0]['response']
        self.player.play(self.tape)
        self.rule.json.assert_called_with(
            response['json'], response['code'], response['headers'])

    def test_should_handle_missing_fields(self):
        response = {
            'code': 200,
            'json': {'id': 42, 'name': 'John', 'last_name': 'Doe'},
        }
        self.tape[0]['response'] = response
        self.player.play(self.tape)
        self.rule.json.assert_called_with(
            response['json'], response['code'], None)


class TextResponseTest(PlayerTest):
    def setUp(self):
        super().setUp()
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
                    'headers': {'Content-Type': 'text/html'},
                    'text': '<h1>Boom</h1>',
                    'json': None,
                }
            }
        ]

    def test_should_respond_with_text(self):
        self.player.play(self.tape)
        response = self.tape[0]['response']
        self.rule.text.assert_called_with(
            response['text'], response['code'], response['headers'])

    def test_should_handle_missing_fields(self):
        response = { 'code': 200 }
        self.tape[0]['response'] = response
        self.player.play(self.tape)
        self.rule.status.assert_called_with(200, None)


class StatusResponseTest(PlayerTest):
    def setUp(self):
        super().setUp()
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
                    'headers': {'Content-Type': 'text/html'},
                    'text': None,
                    'json': None,
                }
            }
        ]

    def test_should_respond_with_status_and_headers(self):
        response = self.tape[0]['response']
        self.player.play(self.tape)
        self.rule.status.assert_called_with(200, response['headers'])

    def test_should_handle_missing_fields(self):
        response = { 'code': 200 }
        self.tape[0]['response'] = response
        self.player.play(self.tape)
        self.rule.status.assert_called_with(200, None)


class HeadersTransformsTest(PlayerTest):
    def setUp(self):
        super().setUp()
        self.tape = [
            {
                'request': {
                    'path': '/api/users',
                    'method': 'POST',
                    'headers': {
                        'Content-Type': 'application/json',
                        'Transfer-Encoding': 'chunked',
                    },
                    'text': None,
                    'json': {'name': 'Dude'},
                },
                'response': {
                    'code': 200,
                    'headers': {'Content-Type': 'text/html'},
                    'text': '<h1>Boom</h1>',
                    'json': None,
                }
            }
        ]

    def test_should_ignore_transfer_encoding(self):
        self.player.play(self.tape)
        self.server.on_json.assert_called_with(
            'POST', '/api/users', {'name': 'Dude'}, {'Content-Type': 'application/json'})

    def test_should_add_cors_header_to_response(self):
        cors_player = Player(self.server, True)
        cors_player.play(self.tape)
        response = self.tape[0]['response']
        self.rule.text.assert_called_with(
            response['text'], response['code'], {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*'
            })


class DecoratorTest(PlayerTest):
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
        - request:
            path: /api/upload
            method: POST
            files:
              bowlers:
                dude: Lebowski
                walter: Sobchak
          response:
            code: 200
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
            {
                'request': {
                    'path': '/api/upload',
                    'method': 'POST',
                    'files': {
                        'bowlers': {
                            'dude': b'Lebowski',
                            'walter': b'Sobchak'
                        }
                    }
                },
                'response': {
                    'code': 200
                }
            }
        ]
        result = tape_from_yaml(text)
        self.assertEqual(expected, result)
