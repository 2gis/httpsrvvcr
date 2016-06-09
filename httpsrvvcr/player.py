'''
VCR Player plays tapes recorded with ``httpsrvvcr.recorder``
using :class:`httpsrv.Server` provided
'''

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
    headers = headers or {}
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
        req_headers = _filter_headers(request['headers'])
        # httpsrv gurantees that json param will have priority over text
        rule = self._server.on(
            request['method'], request['path'], req_headers,
            text=request['text'], json=request['json'])
        self._set_response(rule, response)

    def _set_response(self, rule, response):
        headers = response['headers'] or {}
        if self._add_cors:
            headers['Access-Control-Allow-Origin'] = '*'
        if response['json']:
            rule.json(response['json'], response['code'], headers)
        elif response['text']:
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
        def _wrapper(wrapped):
            def _decorator(*args, **kwargs):
                with open(tape_file_name, 'r', encoding='utf8') as tape_file:
                    tape_yaml = tape_file.read()
                    tape = tape_from_yaml(tape_yaml)
                    self.play(tape)
                    wrapped(*args, **kwargs)
            return _decorator
        return _wrapper

