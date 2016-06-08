'''
VCR Player plays tapes recorded with ``httpsrvvcr.recorder``
using :class:`httpsrv.Server` provided
'''

import yaml


def tape_from_yaml(yaml_text):
    '''
    Parses yaml tape into python dictionary

    :type yaml_text: str
    :param yaml_text: yaml string to parse
    '''
    return yaml.load(yaml_text)


class Player:
    '''
    Player wraps the :class:`httpsrv.Server`
    and plays perviously recorded vcr tapes on it

    :type server: httpsrv.Server
    :param server: server thta will be loaded with rules from vcr tapes
    '''
    def __init__(self, server):
        self._server = server

    def play(self, tape):
        '''
        Loads the server with rules created from tape passed

        :type tape: dict
        :param tape: vcr tape previously recorded with ``httpsrvvcr.recorder``
        '''
        for rule in tape:
            self._set_rule(rule)

    def _set_rule(self, rule):
        request = rule['request']
        response = rule['response']
        # httpsrv gurantees that json param will have priority over text
        rule = self._server.on(
            request['method'], request['path'], request['headers'],
            text=request['text'], json=request['json'])
        if response['json']:
            rule.json(response['json'], response['code'], response['headers'])
        elif response['text']:
            rule.text(response['text'], response['code'], response['headers'])
        else:
            rule.statuc(response['code'], response['headers'])

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

