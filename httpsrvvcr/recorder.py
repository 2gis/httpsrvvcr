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
        dumped = self._yaml.dump(
            data, width=100, default_flow_style=False, allow_unicode=True)
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
    '''
    def __init__(self, writer, json):
        self._writer = writer
        self._json = json

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
        self._writer.write([{
            'request': self._request_output(request),
            'response': self._response_output(response)
        }])

    def _request_output(self, request):
        text_and_json = self._read_text_and_json(request)
        output = {
            'path': request.uri,
            'method': request.method,
            'headers': dict(request.headers),
        }
        output.update(text_and_json)
        return output

    def _response_output(self, response):
        text_and_json = self._read_text_and_json(response)
        code_and_headers = {'code': response.code, 'headers': dict(response.headers)}
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
            body=self.request.body or None)


def run(port, target):
    '''
    Starts a vcr proxy on a given ``port`` using ``target`` as a request destination

    :type port: int
    :param port: port the proxy will bind to

    :type target: str
    :param target: URL to proxy requests to, must be passed with protocol,
        e.g. ``http://some-url.com``
    '''
    vcr_writer = VcrWriter(YamlWriter(sys.stdout, pyyaml), pyjson)
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
    args = parser.parse_args()
    run(args.port, args.target)

