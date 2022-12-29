import typing

from dataclasses import is_dataclass, asdict

from requests_decorator.exceptions import SerialisationException


RequestKwargs = dict

_REQUESTS_KWARGS = ["params", "data", "headers", "cookies", "files", "auth", "timeout", "allow_redirects",
                    "proxies", "hooks", "stream", "verify", "cert", "json"]


class Request:
    media_type = None
    default_model = str

    def __init__(self, request_model=None):
        self._request_model = request_model or self.default_model

    def get_requests_kwargs(self, kwargs):
        requests_kwargs = dict(filter(lambda kv_pair: kv_pair[0] in _REQUESTS_KWARGS, kwargs.items()))
        headers = kwargs.get("headers")
        if headers:
            requests_kwargs["headers"] = self.serialise_headers(headers)
        data = kwargs.get("data")
        if data:
            requests_kwargs["data"] = self.serialise_data(data)
        return requests_kwargs

    def serialise_headers(self, headers):
        serialised_headers = dict()
        for key, value in headers.items():
            if is_dataclass(value):
                serialised_headers[key] = asdict(value)
            else:
                serialised_headers[key] = value
        return serialised_headers

    def serialise_data(self, content):
        return self._request_model(content)


class TextRequest(Request):
    media_type = "text/plain"


class JsonRequest(Request):
    media_type = "application/json"
    default_model = dict

    def __init__(self, request_model=None):
        self._is_request_model = request_model is not None
        self._is_list_request_model = typing.get_origin(request_model) is list
        super().__init__(
            request_model=request_model if not self._is_list_request_model else typing.get_args(request_model)[0]
        )

    def serialise_data(self, data):
        is_list_object = isinstance(data, list)
        if self._is_request_model and type(self._request_model) != type(data):
            if is_list_object and not self._is_list_request_model:
                raise SerialisationException(
                    "Unable to serialise request. Request is a list but 'request_model' defined is not."
                )
            elif not is_list_object and self._is_list_request_model:
                raise SerialisationException(
                    "Unable to serialise request. 'request_model' defined a list but request was not a list."
                )
            raise SerialisationException(
                "Unable to serialise request. Request data type does not match type defined by 'request_model'."
            )
        if is_list_object:
            return [asdict(data_item) for data_item in data]
        return asdict(data)


REQUEST_DECORATORS = [
    Request,
    TextRequest,
    JsonRequest
]


def get_request(headers, request_model=None, request_class: typing.Type[Request] = None) -> Request:
    if request_class:
        return request_class(request_model=request_model)
    else:
        content_type = headers.get('content-type', None)
        for request_decorator in REQUEST_DECORATORS:
            if content_type == request_decorator.media_type:
                return request_decorator(request_model=request_model)
        raise SerialisationException(
            f"Unable to provide request serialiser. Request content-type {content_type} is not supported."
        )
