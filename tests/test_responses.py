import dataclasses

import pydantic
import pytest
import requests

from requests_decorator.exceptions import SerialisationException
from requests_decorator.responses import Response, TextResponse, JsonResponse, decorate_response


@dataclasses.dataclass
class TestStdDataclass:
    foo: str
    bar: int


@pydantic.dataclasses.dataclass
class TestPydanticDataclass:
    foo: str
    bar: int


class TestResponse:
    @dataclasses.dataclass
    class TestModel:
        foo: str

    def setup_method(self):
        self._response = requests.Response()

    def test_media_type_is_none(self):
        result = Response(self._response)
        assert result.media_type is None

    def test_default_model_is_str(self):
        result = Response(self._response)
        assert result.default_model is str

    def test_response_when_initialised_with_requests_response_then_returns_decorated_response_class(self):
        result = Response(self._response)
        assert hasattr(result, "_response_model")
        assert hasattr(result, "deserialise_content")

    def test_deserialise_content_when_response_model_then_returns_initialised_response_model(self):
        response = Response(self._response, response_model=TestResponse.TestModel)
        result = response.deserialise_content()
        assert isinstance(result, TestResponse.TestModel)

    def test_deserialise_content_when_no_response_model_then_returns_initialised_default_response_model(self):
        response = Response(self._response)
        result = response.deserialise_content()
        assert isinstance(result, Response.default_model)


class TestTextResponse:
    def setup_method(self):
        self._response = requests.Response()

    def test_media_type_is_plain_text(self):
        result = TextResponse(self._response)
        assert result.media_type == "text/plain"

    def test_default_model_is_str(self):
        result = TextResponse(self._response)
        assert result.default_model is str


class TestJsonResponse:

    def setup_method(self):
        self._response = requests.Response()
        self._response.status_code = 200

    def test_media_type_is_plain_text(self):
        result = JsonResponse(self._response)
        assert result.media_type == "application/json"

    def test_default_model_is_str(self):
        result = JsonResponse(self._response)
        assert result.default_model is dict

    def test_response_when_initialised_with_std_dataclass_response_model_then_changes_to_pydantic_dataclass(self):
        result = JsonResponse(self._response, response_model=TestStdDataclass)
        assert dataclasses.is_dataclass(result._response_model)
        assert not pydantic.dataclasses.is_builtin_dataclass(result._response_model)

    def test_deserialise_content_when_response_model_then_returns_initialised_response_model(self):
        self._response._content = str.encode('{"foo": "moo", "bar": 0}')
        response = JsonResponse(self._response, response_model=TestPydanticDataclass)
        result = response.deserialise_content()
        assert isinstance(result, TestPydanticDataclass)
        assert result.foo == "moo"
        assert result.bar == 0

    def test_deserialise_content_when_no_response_model_then_returns_initialised_default_response_model(self):
        self._response._content = str.encode('{"foo": "moo", "bar": 0}')
        response = JsonResponse(self._response)
        result = response.deserialise_content()
        assert isinstance(result, JsonResponse.default_model)
        assert result["foo"] == "moo"
        assert result["bar"] == 0

    def test_deserialise_content_when_response_model_and_content_is_list_then_returns_initialised_response_model_list(self):
        self._response._content = str.encode('[{"foo": "moo", "bar": 0}, {"foo": "baz", "bar": 1}]')
        response = JsonResponse(self._response, response_model=list[TestPydanticDataclass])
        result = response.deserialise_content()
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], TestPydanticDataclass)
        assert isinstance(result[1], TestPydanticDataclass)

    def test_deserialise_content_when_response_model_is_list_and_content_is_not_list_then_raise_error(self):
        self._response._content = str.encode('{"foo": "moo", "bar": 0}')
        response = JsonResponse(self._response, response_model=list[TestPydanticDataclass])
        with pytest.raises(Exception) as error:
            response.deserialise_content()
        assert error
        assert error.type == SerialisationException
        assert error.value.args[0] == \
               "Unable to deserialise response. 'response_model' defined a list but response was not a list."

    def test_deserialise_content_when_response_model_is_not_list_and_content_is_list_then_raise_error(self):
        self._response._content = str.encode('[{"foo": "moo", "bar": 0}, {"foo": "baz", "bar": 1}]')
        response = JsonResponse(self._response, response_model=TestPydanticDataclass)
        with pytest.raises(Exception) as error:
            response.deserialise_content()
        assert error
        assert error.type == SerialisationException
        assert error.value.args[0] == \
               "Unable to deserialise response. Response is a list but 'response_model' defined is not."


def test_decorate_response_when_response_class_then_return_response_class_instance():
    response = requests.Response()
    result = decorate_response(response, str, response_class=TextResponse)
    assert isinstance(result, TextResponse)


def test_decorate_response_when_content_type_is_none_then_return_response_instance():
    response = requests.Response()
    response.headers["content-type"] = None
    result = decorate_response(response, str)
    assert isinstance(result, Response)


def test_decorate_response_when_content_type_is_text_then_return_text_response_instance():
    response = requests.Response()
    response.headers["content-type"] = "text/plain"
    result = decorate_response(response, str)
    assert isinstance(result, TextResponse)


def test_decorate_response_when_content_type_is_json_then_return_json_response_instance():
    response = requests.Response()
    response.headers["content-type"] = "application/json"
    result = decorate_response(response, dict)
    assert isinstance(result, JsonResponse)


def test_decorate_response_when_content_type_is_not_recognised_then_raise_error():
    response = requests.Response()
    response.headers["content-type"] = "foobar"
    with pytest.raises(Exception) as error:
        decorate_response(response, str)
    assert error
    assert error.type == SerialisationException
    assert error.value.args[0] == \
           "Unable to provide response serialiser. Response content-type 'foobar' is not supported."
