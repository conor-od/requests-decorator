import inspect

from requests import Session

from requests_decorator.exceptions import ArgumentError
from requests_decorator.requests import get_request
from requests_decorator.responses import decorate_response
from utils import deep_concat


# TODO - Unit Test
class RequestRouter:

    def __init__(self, url, path='', session=None, **requests_kwargs):
        self._url = url
        self._path = path
        self._session = session
        self._router_requests_kwargs = requests_kwargs

    def get(self,
            path,
            session=None,
            request_model=None,
            request_class=None,
            response_model=None,
            response_class=None,
            **decorator_kwargs):
        return self.request(
            "GET",
            path,
            session=session,
            request_model=request_model,
            request_class=request_class,
            response_model=response_model,
            response_class=response_class,
            **decorator_kwargs
        )

    def post(self,
             path,
             session=None,
             request_model=None,
             request_class=None,
             response_model=None,
             response_class=None,
             **decorator_kwargs):
        return self.request(
            "POST",
            path,
            session=session,
            request_model=request_model,
            request_class=request_class,
            response_model=response_model,
            response_class=response_class,
            **decorator_kwargs
        )

    def put(self,
            path,
            session=None,
            request_model=None,
            request_class=None,
            response_model=None,
            response_class=None,
            **decorator_kwargs):
        return self.request(
            "PUT",
            path,
            session=session,
            request_model=request_model,
            request_class=request_class,
            response_model=response_model,
            response_class=response_class,
            **decorator_kwargs
        )

    def patch(self,
              path,
              session=None,
              request_model=None,
              request_class=None,
              response_model=None,
              response_class=None,
              **decorator_kwargs):
        return self.request(
            "PATCH",
            path,
            session=session,
            request_model=request_model,
            request_class=request_class,
            response_model=response_model,
            response_class=response_class,
            **decorator_kwargs
        )

    def delete(self,
               path,
               session=None,
               request_model=None,
               request_class=None,
               response_model=None,
               response_class=None,
               **decorator_kwargs):
        return self.request(
            "DELETE",
            path,
            session=session,
            request_model=request_model,
            request_class=request_class,
            response_model=response_model,
            response_class=response_class,
            **decorator_kwargs
        )

    def head(self,
             path,
             session=None,
             request_model=None,
             request_class=None,
             response_model=None,
             response_class=None,
             **decorator_kwargs):
        return self.request(
            "HEAD",
            path,
            session=session,
            request_model=request_model,
            request_class=request_class,
            response_model=response_model,
            response_class=response_class,
            **decorator_kwargs
        )

    def options(self,
                path,
                session=None,
                request_model=None,
                request_class=None,
                response_model=None,
                response_class=None,
                **decorator_kwargs):
        return self.request(
            "OPTIONS",
            path,
            session=session,
            request_model=request_model,
            request_class=request_class,
            response_model=response_model,
            response_class=response_class,
            **decorator_kwargs
        )

    def request(self,
                method,
                path,
                session=None,
                request_model=None,
                request_class=None,
                response_model=None,
                response_class=None,
                return_response_class=False,
                **decorator_kwargs):
        session = session or self._session or Session()

        def decorator(function):
            def wrapper(*args, **kwargs):
                self._validate_kwargs(kwargs, return_response_class)
                function_arguments = self._get_function_arguments_as_dict(function, args, kwargs)
                url = self._build_url(path, function_arguments)
                request_kwargs = self._build_requests_kwargs(
                    decorator_kwargs, function_arguments, request_model=request_model, request_class=request_class
                )
                response = session.request(method, url, **request_kwargs)
                response = decorate_response(response, response_model, response_class=response_class)
                if return_response_class:
                    try:
                        return function(*args, **kwargs, response=response) or response
                    except TypeError:
                        raise ArgumentError("'response' keyword argument is required to return response.")
                response.raise_for_status()
                return response.deserialise_content()

            return wrapper
        return decorator

    @staticmethod
    def _validate_kwargs(kwargs, return_response_class):
        if kwargs.get("response", None) and not return_response_class:
            raise ArgumentError("'response' is a reserved keyword argument.")

    @staticmethod
    def _get_function_arguments_as_dict(function, args, kwargs):
        return dict(inspect.signature(function).bind(*args, **kwargs).arguments)

    def _build_requests_kwargs(self, decorator_kwargs, function_arguments, request_model=None, request_class=None):
        arguments = deep_concat(self._router_requests_kwargs, decorator_kwargs)
        arguments = deep_concat(arguments, function_arguments)
        request = get_request(arguments.get("header"), request_model, request_class)
        return request.get_requests_kwargs(arguments)

    def _build_url(self, path, function_arguments):
        return f"{self._url}{self._path}{path}".format(**function_arguments)
