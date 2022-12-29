import dataclasses

import pydantic.dataclasses
import pytest

from requests_decorator.exceptions import SerialisationException
from requests_decorator.requests import Request, RequestKwargs, TextRequest, JsonRequest


@dataclasses.dataclass
class TestStdDataclass:
    foo: str


@pydantic.dataclasses.dataclass
class TestPydanticDataclass:
    foo: str


class TestRequest:

    def setup_method(self):
        self._request = Request()

    def test_request_get_requests_kwargs_when_many_kwargs_return_request_kwargs_only(self):
        kwargs = RequestKwargs(headers={"content": "example"}, data="here be some string data", fizz="buzz")
        result = self._request.get_requests_kwargs(kwargs)
        assert result
        assert len(result) is 2
        assert result.get("headers")
        assert result.get("data")

    def test_serialise_headers_when_header_is_std_dataclass_return_serialised_headers(self):
        headers = {"example": TestStdDataclass(foo="bar")}
        result = self._request.serialise_headers(headers)
        assert result
        assert result == {"example": {"foo": "bar"}}

    def test_serialise_headers_when_header_is_pydantic_dataclass_return_serialised_headers(self):
        headers = {"example": TestPydanticDataclass(foo="bar")}
        result = self._request.serialise_headers(headers)
        assert result
        assert result == {"example": {"foo": "bar"}}

    def test_request_get_requests_kwargs_when_no_kwargs_return_empty_dict(self):
        kwargs = RequestKwargs()
        request_kwargs = self._request.get_requests_kwargs(kwargs)
        assert isinstance(request_kwargs, dict)
        assert request_kwargs == {}

    def test_media_type_is_none(self):
        assert self._request.media_type is None

    def test_default_data_model_is_str(self):
        assert self._request.default_model is str


class TestTextRequest:
    def setup_method(self):
        self._request = TextRequest()

    def test_media_type_is_text(self):
        assert self._request.media_type == "text/plain"

    def test_default_data_model_is_str(self):
        assert self._request.default_model is str


class TestJsonRequest:
    def setup_method(self):
        self._request = JsonRequest()

    def test_media_type_is_json(self):
        assert self._request.media_type == "application/json"

    def test_default_data_model_is_str(self):
        assert self._request.default_model is dict

    def test_serialise_data_when_data_is_std_dataclass_return_serialised_data(self):
        data = TestStdDataclass(foo="bar")
        result = self._request.serialise_data(data)
        assert result
        assert result == {"foo": "bar"}

    def test_serialise_data_when_data_is_pydantic_dataclass_return_serialised_data(self):
        data = TestPydanticDataclass(foo="bar")
        result = self._request.serialise_data(data)
        assert result
        assert result == {"foo": "bar"}

    def test_serialise_data_when_data_is_list_of_dataclass_return_serialised_data(self):
        data = [TestPydanticDataclass(foo="bar"), TestPydanticDataclass(foo="baz")]
        result = self._request.serialise_data(data)
        assert result
        assert result == [{"foo": "bar"}, {"foo": "baz"}]

    def test_serialise_data_when_data_is_list_and_model_not_then_raise_error(self):
        data = [TestPydanticDataclass(foo="bar")]
        with pytest.raises(Exception) as error:
            JsonRequest(request_model=TestPydanticDataclass).serialise_data(data)
        assert error
        assert error.type == SerialisationException
        assert error.value.args[0] == \
               "Unable to serialise request. Request is a list but 'request_model' defined is not."

    def test_serialise_data_when_data_is_dataclass_and_model_is_list_then_raise_error(self):
        data = TestPydanticDataclass(foo="bar")
        with pytest.raises(Exception) as error:
            JsonRequest(request_model=list[TestPydanticDataclass]).serialise_data(data)
        assert error
        assert error.type == SerialisationException
        assert error.value.args[0] == \
               "Unable to serialise request. 'request_model' defined a list but request was not a list."

    def test_serialise_data_when_data_and_model_type_dont_match_then_raise_error(self):
        data = TestPydanticDataclass(foo="bar")
        with pytest.raises(Exception) as error:
            JsonRequest(request_model=TestStdDataclass).serialise_data(data)
        assert error
        assert error.type == SerialisationException
        assert error.value.args[0] == \
               "Unable to serialise request. Request data type does not match type defined by 'request_model'."
