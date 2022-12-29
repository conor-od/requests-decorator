import typing
from dataclasses import is_dataclass
from typing import Type

import pydantic
import requests

from requests_decorator.exceptions import SerialisationException


class Response(requests.Response):
    media_type = None
    default_model = str

    def __init__(self, response: requests.Response, response_model=None):
        self.__class__ = type(response.__class__.__name__,
                              (self.__class__, response.__class__),
                              {})
        self.__dict__ = response.__dict__
        self._response_model = response_model or self.default_model

    def deserialise_content(self):
        return self._response_model(self.content)


class TextResponse(Response):
    media_type = "text/plain"


class JsonResponse(Response):
    media_type = "application/json"
    default_model = dict

    def __init__(self, response: requests.Response, response_model=None):
        is_list_response_model = typing.get_origin(response_model) is list
        super().__init__(
            response,
            response_model=response_model if not is_list_response_model else typing.get_args(response_model)[0]
        )
        self._is_response_model = response_model is not None
        self._is_list_response_model = is_list_response_model
        if is_dataclass(self._response_model):
            # Decorate std dataclass with pydantic dataclass
            pydantic.dataclasses.dataclass(self._response_model)

    def deserialise_content(self):
        json_body = self.json()
        is_list_json_body = isinstance(json_body, list)
        if self._is_response_model and is_list_json_body != self._is_list_response_model:
            if is_list_json_body and not self._is_list_response_model:
                raise SerialisationException(
                    "Unable to deserialise response. Response is a list but 'response_model' defined is not."
                )
            raise SerialisationException(
                "Unable to deserialise response. 'response_model' defined a list but response was not a list."
            )
        if is_list_json_body:
            return [self._response_model(**json_item) for json_item in json_body]
        return self._response_model(**json_body)


RESPONSE_DECORATORS = [
    Response,
    TextResponse,
    JsonResponse
]


def decorate_response(response: requests.Response, response_model, response_class: Type[Response] = None) -> Response:
    if response_class:
        return response_class(response, response_model=response_model)
    else:
        content_type = response.headers.get('content-type', None)
        for response_decorator in RESPONSE_DECORATORS:
            if content_type == response_decorator.media_type:
                return response_decorator(response, response_model=response_model)
        raise SerialisationException(
            f"Unable to provide response serialiser. Response content-type '{content_type}' is not supported."
        )
