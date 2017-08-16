from requests.exceptions import HTTPError


class ApiHttpError(HTTPError):

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        for key in kwargs:
            setattr(self, key, kwargs[key])


class HttpClientError(ApiHttpError):
    pass


class Unauthorized(HttpClientError):
    pass


class Forbidden(HttpClientError):
    pass


class HttpNotFoundError(HttpClientError):
    pass


class HttpServerError(ApiHttpError):
    pass
