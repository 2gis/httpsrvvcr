import unittest
from unittest.mock import Mock, MagicMock, call

from tornado.testing import AsyncTestCase, gen_test
from tornado.concurrent import Future

from httpsrvvcr import recorder


def future_mock(value):
    fut = Future()
    fut.set_result(value)
    return Mock(return_value=fut)


def response_mock():
    response = Mock()
    response.code = 200
    response.body = b'Response body'
    response.headers = {'Content-Type': 'text/plain', 'Content-Length': 100}
    return response


def client_mock(response):
    client = Mock()
    client.fetch = future_mock(response)
    return client


def create_handler(request, client, target, writer):
    handler = recorder.ProxyHandler(
        MagicMock(), request, httpclient=client, target=target, writer=writer)
    handler.set_status = Mock()
    handler.finish = Mock()
    handler.write = Mock()
    handler.set_header = Mock()
    return handler


def request_mock():
    request = Mock()
    request.method = 'GET'
    request.headers = {'Accept': 'appliaction/json'}
    request.body = None
    request.uri = '/'
    return request


class ProxyHandlerTest(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.response = response_mock()
        self.client = client_mock(self.response)
        self.target = 'http://nowhere.com'
        self.request = request_mock()
        self.writer = Mock()
        self.handler = create_handler(self.request, self.client, self.target, self.writer)

    @gen_test
    def test_should_fetch_target_url(self):
        yield self.handler.prepare()
        self.client.fetch.assert_called_with(
            self.target + self.request.uri,
            method=self.request.method,
            headers=self.request.headers,
            allow_nonstandard_methods=True,
            body=self.request.body)

    @gen_test
    def test_should_respond_with_target_code(self):
        yield self.handler.prepare()
        self.handler.set_status.assert_called_with(self.response.code)

    @gen_test
    def test_should_respond_with_target_body(self):
        yield self.handler.prepare()
        self.handler.write.assert_called_with(self.response.body)

    @gen_test
    def test_should_respond_with_target_headers(self):
        yield self.handler.prepare()
        self.handler.set_header.assert_has_calls([
            call('Content-Length', 100),
            call('Content-Type', 'text/plain')], any_order=True)

    @gen_test
    def test_should_finish_request(self):
        yield self.handler.prepare()
        self.handler.finish.assert_called_with()

    @gen_test
    def test_should_record_response(self):
        yield self.handler.prepare()
        self.writer.write.assert_called_with(self.request, self.response)

    @gen_test
    def test_should_set_cors_header(self):
        yield self.handler.prepare()
        self.handler.set_header.assert_called_with(
            'Access-Control-Allow-Origin', '*')

    @gen_test
    def test_should_exclude_headers_in_response(self):
        self.response.headers['Transfer-Encoding'] = 'chunked'
        yield self.handler.prepare()
        self.assertNotIn((('Transfer-Encoding', 'chunked'),), self.handler.set_header.call_args_list)


class YamlWriterTest(unittest.TestCase):
    def setUp(self):
        self.wrapped_writer = Mock()
        self.dumped = 'dumped yaml here'
        self.yaml = Mock()
        self.yaml.dump = Mock(return_value=self.dumped)
        self.ywriter = recorder.YamlWriter(self.wrapped_writer, self.yaml)
        self.data = {'something': 'here'}

    def test_should_dump_yaml(self):
        self.ywriter.write(self.data)
        self.yaml.dump.assert_called_with(
            self.data, default_flow_style=False, allow_unicode=True)

    def test_should_write_to_wrapped_writer(self):
        self.ywriter.write(self.data)
        self.wrapped_writer.write.assert_called_with(self.dumped)


class VcrWriterTest(unittest.TestCase):
    def setUp(self):
        self.request = request_mock()
        self.response = response_mock()
        self.wrapped_writer = Mock()
        self.parsed_json = {'json': True}
        self.json = Mock()
        self.json.loads = Mock(return_value=self.parsed_json)
        self.writer = recorder.VcrWriter(self.wrapped_writer, self.json)

    def test_should_write_request_and_response(self):
        self.writer.write(self.request, self.response)
        self.wrapped_writer.write.assert_called_with([{
            'request': {
                'path': self.request.uri,
                'method': self.request.method,
                'headers': self.request.headers,
                'text': self.request.body,
                'json': None,
            },
            'response': {
                'code': self.response.code,
                'headers': self.response.headers,
                'text': self.response.body.decode('utf8'),
                'json': None,
            },
        }])

    def test_should_parse_request_json(self):
        self.request.headers['Content-Type'] = 'application/json'
        self.request.body = b'request json'
        self.writer.write(self.request, self.response)
        self.json.loads.assert_called_with(self.request.body.decode('utf8'))

    def test_should_parse_response_json(self):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.body = b'response json'
        self.writer.write(self.request, self.response)
        self.json.loads.assert_called_with(self.response.body.decode('utf8'))

    def test_should_write_response_json(self):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.body = b'response json'
        self.writer.write(self.request, self.response)
        self.wrapped_writer.write.assert_called_with([{
            'request': {
                'path': self.request.uri,
                'method': self.request.method,
                'headers': self.request.headers,
                'text': self.request.body,
                'json': None,
            },
            'response': {
                'code': self.response.code,
                'headers': self.response.headers,
                'text': None,
                'json': self.parsed_json,
            },
        }])

    def test_should_write_request_json(self):
        self.request.headers['Content-Type'] = 'application/json'
        self.request.body = b'response json'
        self.writer.write(self.request, self.response)
        self.wrapped_writer.write.assert_called_with([{
            'request': {
                'path': self.request.uri,
                'method': self.request.method,
                'headers': self.request.headers,
                'json': self.parsed_json,
                'text': None,
            },
            'response': {
                'code': self.response.code,
                'headers': self.response.headers,
                'text': self.response.body.decode('utf8'),
                'json': None,
            },
        }])

    def test_should_write_no_headers(self):
        writer = recorder.VcrWriter(self.wrapped_writer, self.json, True)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.body = b'response json'
        writer.write(self.request, self.response)
        self.wrapped_writer.write.assert_called_with([{
            'request': {
                'path': self.request.uri,
                'method': self.request.method,
                'headers': None,
                'text': self.request.body,
                'json': None,
            },
            'response': {
                'code': self.response.code,
                'headers': None,
                'text': None,
                'json': self.parsed_json,
            },
        }])



