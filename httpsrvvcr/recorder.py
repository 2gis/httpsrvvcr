'''
VCR recorder for httpsrv API mocking library.
Works as a proxy recording real API calls to yaml "vcr tape"
that can further be used as httpsrv fixture
'''

import sys
import argparse
import json as pyjson

import yaml as pyyaml
import tornado.ioloop
import tornado.web
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient, HTTPError


# We don't support chunked encoding for now
EXCLUDED_HEADERS = ['Transfer-Encoding']


class YamlWriter:
    '''
    Acts as a decorator for the wrapped writer object.
    Any data given to :func:`YamlWriter.write` will be converted to
    yaml string and passde to the underlying writer

    :type writer: object
    :param writer: writer object that will recieve yaml string. Must support ``write(str)``

    :type yaml: yaml
    :param yaml: yaml encoder, must support pyyaml-like interface
    '''
    def __init__(self, writer, yaml):
        self._writer = writer
        self._yaml = yaml

    def write(self, data):
        '''
        Writes given data as a yaml string to an underlying stream

        :type data: any
        :param data: object that will be conveted to yaml string
        '''
        dumped = self._yaml.dump(data, default_flow_style=False, allow_unicode=True)
        self._writer.write(dumped)


class VcrWriter:
    '''
    Converts :class:`tornado.httputil.HTTPServerRequest` and
    :class:`tornado.httpclient.HTTPResponse` objects into
    a vcr output utilizing an underlying writer

    :type writer: object
    :param writer: writer object that supports ``write(data)`` interface

    :type json: json
    :param json: json module from standard library

    :type no_headers: bool
    :param no_headers: if ``True`` then no headers will be recorded for request or resposne
    '''
    def __init__(self, writer, json, no_headers=False, skip_methods=None):
        self._writer = writer
        self._json = json
        self._no_headers = no_headers
        self._skip_methods = skip_methods or []

    def write(self, request, response):
        '''
        Writes a vcr output in a form of a dict from given
        :class:`tornado.httputil.HTTPServerRequest`
        and :class:`tornado.httpclient.HTTPResponse`

        :type request: tornado.httputil.HTTPServerRequest
        :param request: server request

        :type response: tornado.httpclient.HTTPResponse
        :param response: client response
        '''
        if request.method in self._skip_methods:
            return
        self._writer.write([{
            'request': self._request_output(request),
            'response': self._response_output(response)
        }])

    def _request_output(self, request):
        text_and_json = self._read_text_and_json(request)
        output = {
            'path': request.uri,
            'method': request.method,
            'headers': None if self._no_headers else dict(request.headers),
        }
        output.update(text_and_json)
        return output

    def _response_output(self, response):
        text_and_json = self._read_text_and_json(response)
        code_and_headers = {
            'code': response.code,
            'headers': None if self._no_headers else dict(response.headers),
        }
        code_and_headers.update(text_and_json)
        return code_and_headers

    def _read_text_and_json(self, data):
        json_body = None
        text_body = data.body.decode('utf8') if data.body else None
        if text_body and 'application/json' in data.headers.get('Content-Type', []):
            json_body = self._json.loads(text_body)
            text_body = None
        return {'text': text_body, 'json': json_body}



class ProxyHandler(tornado.web.RequestHandler):
    '''
    Implementation of a :class:`tornado.web.RequestHandler` that
    proxies any recieved request to a target URL and
    recorders everything that passes through into a given writer
    '''

    def initialize(self, httpclient, target, writer):
        '''
        Initializes a handler, overrides standard :class:`tornado.web.RequestHandler`
        method

        :type httpclient: tornado.httpclient.AsyncHTTPClient
        :param httpclient: httpclient that will be used to make requests to target URL

        :type target: str
        :param target: target API URL to proxy requests to

        :type writer: VcrWriter
        :param writer: vcr writer that will be used to output recorded requests
        '''
        self._httpclient = httpclient
        self._target = target
        self._writer = writer

    @coroutine
    def prepare(self):
        res = yield self._make_request()
        self._writer.write(self.request, res)
        if res.body:
            self.write(res.body)
        self.set_status(res.code)
        for name, value in res.headers.items():
            if name not in EXCLUDED_HEADERS:
                self.set_header(name, value)
        self.set_header('Access-Control-Allow-Origin', '*')
        self.finish()

    @coroutine
    def _make_request(self):
        try:
            res = yield self._proxy_request()
            return res
        except HTTPError as error:
            if not error.response:
                raise error
            return error.response


    def _proxy_request(self):
        return self._httpclient.fetch(
            self._target + self.request.uri,
            method=self.request.method,
            headers=self.request.headers,
            allow_nonstandard_methods=True,
            body=self.request.body or None)


def run(port, target, no_headers=False, skip_methods=None):
    '''
    Starts a vcr proxy on a given ``port`` using ``target`` as a request destination

    :type port: int
    :param port: port the proxy will bind to

    :type target: str
    :param target: URL to proxy requests to, must be passed with protocol,
        e.g. ``http://some-url.com``

    :type no_headers: bool
    :param no_headers: if ``True`` then no headers will be recorded for request or resposne

    :type skip_methods: list
    :param skip_methods: recorder will not write any requests with provided methods to output
    '''
    vcr_writer = VcrWriter(YamlWriter(sys.stdout, pyyaml), pyjson, no_headers, skip_methods)
    app = tornado.web.Application([
        (r'.*', ProxyHandler, dict(httpclient=AsyncHTTPClient(), target=target, writer=vcr_writer))
    ])
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()

def stop():
    '''
    Stops currently running vcr proxy
    '''
    tornado.ioloop.IOLoop.current().stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Recording proxy for httpsrv library', prog='python -m httpsrvvcr.recorder')
    parser.add_argument('port', help='port our proxy will be binded to', type=int)
    parser.add_argument('target', help='destination server URL including protocol', type=str)
    parser.add_argument('--no-headers', help='do not record any headers',
                        action='store_const', const=True, default=False)
    parser.add_argument('--skip-methods', help='method to skip, can pass multiple times',
                        type=str, nargs='*', default=[])
    args = parser.parse_args()
    run(args.port, args.target, args.no_headers, args.skip_methods)

