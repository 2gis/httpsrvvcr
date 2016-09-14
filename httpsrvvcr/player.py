'''
VCR Player plays tapes recorded with ``httpsrvvcr.recorder``
using :class:`httpsrv.Server` provided
'''

from functools import wraps

import yaml


_IGNORE_HEADERS = [
    'transfer-encoding'
]


def tape_from_yaml(yaml_text):
    '''
    Parses yaml tape into python dictionary

    :type yaml_text: str
    :param yaml_text: yaml string to parse
    '''
    return yaml.load(yaml_text)


def _filter_headers(headers):
    if not headers:
        return None
    return dict((name, value) for name, value in headers.items()
                if name.lower() not in _IGNORE_HEADERS)


class Player:
    '''
    Player wraps the :class:`httpsrv.Server`
    and plays perviously recorded vcr tapes on it

    :type server: httpsrv.Server
    :param server: server thta will be loaded with rules from vcr tapes

    :type add_cors: bool
    :param add_cors: if ``True`` player will add CORS header to all responses
    '''
    def __init__(self, server, add_cors=False):
        self._server = server
        self._add_cors = add_cors

    def play(self, tape):
        '''
        Loads the server with rules created from tape passed

        :type tape: dict
        :param tape: vcr tape previously recorded with ``httpsrvvcr.recorder``
        '''
        for rule in tape:
            self._set_rule(rule)

    def _set_rule(self, action):
        request = action['request']
        response = action['response']

        rule = self._create_rule(request)
        self._set_response(rule, response)

    def _create_rule(self, request):
        headers = _filter_headers(request.get('headers'))
        if request.get('files'):
            return self._new_files_rule(request, headers)
        elif request.get('json'):
            return self._new_json_rule(request, headers)
        elif request.get('form'):
            return self._new_form_fule(request, headers)
        elif request.get('text'):
            return self._new_text_rule(request, headers)
        return self._new_any_rule(request, headers)

    def _new_files_rule(self, request, headers):
        return self._server.on_files(
            request['method'],
            request['path'],
            request['files'],
            request.get('form'),
            headers)

    def _new_json_rule(self, request, headers):
        return self._server.on_json(
            request['method'], request['path'], request['json'], headers)

    def _new_form_fule(self, request, headers):
        return self._server.on_form(
            request['method'], request['path'], request['form'], headers)

    def _new_text_rule(self, request, headers):
        return self._server.on_text(
            request['method'], request['path'], request['text'], headers)

    def _new_any_rule(self, request, headers):
        return self._server.on_any(request['method'], request['path'], headers)

    def _set_response(self, rule, response):
        headers = response.get('headers')
        if self._add_cors:
            headers['Access-Control-Allow-Origin'] = '*'
        if response.get('json'):
            rule.json(response['json'], response['code'], headers)
        elif response.get('text'):
            rule.text(response['text'], response['code'], headers)
        else:
            rule.status(response['code'], headers)

    def load(self, tape_file_name):
        '''
        Decorator that can be used on test functions to read vcr tape from file
        and load current player with it::

            @player.load('path/to/tape.yaml')
            def test_should_do_some_vcr(self):
                pass

        :type tape_file_name: str
        :param tape_file_name: tape filename to load
        '''
        def _decorator(wrapped):
            @wraps(wrapped)
            def _wrapper(*args, **kwargs):
                with open(tape_file_name, 'r', encoding='utf8') as tape_file:
                    tape_yaml = tape_file.read()
                    tape = tape_from_yaml(tape_yaml)
                    self.play(tape)
                    wrapped(*args, **kwargs)
            return _wrapper
        return _decorator

