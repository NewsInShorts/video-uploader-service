import uuid
import logging
import contextvars
from app.config import Config
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

_request_id_ctx = contextvars.ContextVar("request_id", default="no-request-id")

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = _request_id_ctx.get()
        return True


def setup_logging(app):
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s -> %(levelname)s -> [%(filename)s -> %(funcName)s] -> %(request_id)s -> %(message)s'
    ))
    handler.addFilter(RequestIDFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(Config.LOG_LEVEL)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        _request_id_ctx.set(request_id)

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id(request: Request = None):
    if request is not None and hasattr(request.state, "request_id"):
        return request.state.request_id
    return _request_id_ctx.get()
