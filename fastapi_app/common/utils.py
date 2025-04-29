import os
from asyncio.exceptions import TimeoutError

from aiohttp.client_exceptions import ContentTypeError
from aiohttp.web import HTTPException
# from aiohttp_retry.client import ExponentialRetry, RetryClient # type: ignore
from fastapi.responses import JSONResponse
import openai

from fastapi_app.common import HttpStatusCodeEnum
from fastapi_app.common.errors import errors


def get_embedding(text, model="text-embedding-ada-002"):
    """Get the embedding of the input text using OpenAI's Embed API."""
    openai.api_key = "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"
    return openai.Embedding.create(input=text, model=model)


__all__ = [
    "make_dir",
    "exception_handler",
    "custom_exception_handler",
    "is_success_request",
    "invoke_http_request",
]


def make_dir(directory_path):
    """Make directory on requested path
    :param directory_path - Path where dictionary creates
    """

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def exception_handler(req, exc):
    """Exception Handler
    :param req - Request object
    :param exc - Exception

    :returns - Generic error response with status code 500
    """

    return JSONResponse(content=errors["Exception"], status_code=500)


def custom_exception_handler(req, exc):
    """Custom exception handler
    :param req - Request object
    :param exc - Exception

    :returns - Define error message for custom exception
    """

    req.app.logger.info(f"Custom Exception {exc.__class__.__name__} on {req.url.path}")
    return JSONResponse(
        content=errors.get(exc.__class__.__name__, errors["Exception"]),
        status_code=errors.get(exc.__class__.__name__, errors["Exception"])["status"],
    )


def is_success_request(status_code):
    """Check is success response or not
    :param status_code - Status code

    :return - Boolean
    """

    return 200 <= status_code <= 299


def requests_retry_session():
    """Add retry session for HttpRequest"""

    retry_option = ExponentialRetry(
        attempts=3,
        start_timeout=0.5,
        factor=1.5,
        statuses=(
            HttpStatusCodeEnum.RATE_LIMIT.value,
            HttpStatusCodeEnum.INTERNAL_SERVER_ERROR.value,
            HttpStatusCodeEnum.BAD_GATEWAY.value,
            HttpStatusCodeEnum.SERVICE_UNAVAILABLE.value,
            HttpStatusCodeEnum.GATEWAY_TIMEOUT.value,
        ),
    )
    return retry_option


async def _get_response(response):
    """Get json/text response"""

    try:
        return await response.json()
    except ContentTypeError:
        return await response.text()


async def invoke_http_request(endpoint, method, headers={}, payload={}, timeout=60):
    """HttpRequest Maker
    :param  endpoint - URL
    :param method - Http Method
    :param headers - Request header
    :param payload - Request body
    :param timeout - Request timeout

    :returns - Response & status code from Http request call
    """
    retry_session = requests_retry_session()
    response = status = None
    try:
        async with RetryClient(retry_options=retry_session, headers=headers) as session:
            async with session.request(
                method=method, url=endpoint, json=payload, ssl=False, timeout=timeout
            ) as response:
                response, status_code = await _get_response(response), response.status
        return response, status_code
    except HTTPException:
        return response, status
    except TimeoutError:
        return response, status
