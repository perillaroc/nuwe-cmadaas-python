import json
import os
import pathlib
import tempfile
import time
from typing import Callable, Any, Union, Tuple, Optional

import requests

from nuwe_cmadaas._log import logger

from .data import ResponseData


class Connection:
    """HTTP transport used by the MUSIC-compatible client.

    ``requests`` remains the default transport for compatibility. A Session
    or an object exposing ``get`` can be injected for pooling and tests.
    """

    getwayFlag = b'"flag":"slb"'
    otherError = -10001
    httpError = -10002
    decodeError = -10003
    downloadError = -10004
    RETRYABLE_STATUS_CODES = frozenset({502, 503, 504})

    def __init__(
            self,
            connect_timeout: float,
            read_timeout: float,
            session=None,
            transport=None,
            max_retries: int = 2,
            retry_backoff: float = 0.1,
            sleep: Callable[[float], None] = time.sleep,
    ):
        if session is not None and transport is not None:
            raise ValueError("session and transport are mutually exclusive")
        if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        if retry_backoff < 0:
            raise ValueError("retry_backoff must be non-negative")
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.transport = transport if transport is not None else session
        if self.transport is None:
            self.transport = requests
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.sleep = sleep
        self.last_retries = 0

    @property
    def timeout(self) -> tuple[float, float]:
        return self.connect_timeout, self.read_timeout

    def _wait_before_retry(self, retry_number: int) -> None:
        self.sleep(self.retry_backoff * (2 ** (retry_number - 1)))

    @staticmethod
    def _status_code(response) -> int:
        return int(getattr(response, "status_code", 200))

    @classmethod
    def _is_retryable_status(cls, status_code: int) -> bool:
        return status_code in cls.RETRYABLE_STATUS_CODES

    @staticmethod
    def _is_retryable_exception(error: Exception) -> bool:
        return isinstance(error, (requests.Timeout, requests.ConnectionError))

    @staticmethod
    def _gateway_error(response_content: bytes):
        try:
            response_json = json.loads(response_content)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            return None
        if not isinstance(response_json, dict):
            return None
        if "returnCode" not in response_json or "returnMessage" not in response_json:
            return None
        return response_json["returnCode"], response_json["returnMessage"]

    @classmethod
    def _failure_result(cls, response_content: bytes, status_code: int | None = None):
        gateway_error = cls._gateway_error(response_content)
        if gateway_error is not None:
            return gateway_error
        if status_code is not None and not 200 <= status_code < 300:
            return cls.httpError, f"HTTP {status_code} response"
        return cls.otherError, "unrecognized gateway response"

    @classmethod
    def _invoke_failure_handler(cls, failure_handler, response_content, status_code):
        try:
            return failure_handler(response_content, status_code=status_code)
        except TypeError:
            # Preserve the old one-argument callback contract.
            return failure_handler(response_content)

    def make_request(
            self,
            fetch_url: str,
            success_handler: Callable[[bytes], ResponseData],
            failure_handler: Callable[[bytes], ResponseData],
            exception_handler: Callable[[Exception], Any],
            idempotent: bool = True,
    ) -> ResponseData:
        """Fetch and classify a MUSIC response with bounded read retries."""
        self.last_retries = 0
        for attempt in range(self.max_retries + 1):
            response = None
            try:
                response = self.transport.get(
                    fetch_url,
                    timeout=self.timeout,
                    stream=True,
                )
                status_code = self._status_code(response)
                if idempotent and attempt < self.max_retries and self._is_retryable_status(status_code):
                    self.last_retries += 1
                    close = getattr(response, "close", None)
                    if close is not None:
                        close()
                    response = None
                    self._wait_before_retry(self.last_retries)
                    continue

                response_content = response.content
                if not 200 <= status_code < 300:
                    return self._invoke_failure_handler(
                        failure_handler, response_content, status_code
                    )
                if self._check_getway_flag(response_content):
                    return failure_handler(response_content)
                return success_handler(response_content)
            except requests.exceptions.RequestException as error:
                if idempotent and attempt < self.max_retries and self._is_retryable_exception(error):
                    self.last_retries += 1
                    self._wait_before_retry(self.last_retries)
                    continue
                return exception_handler(error)
            finally:
                if response is not None:
                    close = getattr(response, "close", None)
                    if close is not None:
                        close()

        raise AssertionError("request retry loop did not return")

    def download_file(
        self,
        file_url: str,
        save_file: Union[str, pathlib.Path],
        *,
        overwrite: bool = True,
        chunk_size: int = 1024 * 1024,
    ) -> Tuple[int, Optional[str]]:
        """Stream a file to a same-directory temporary file and replace atomically."""
        destination = pathlib.Path(save_file)
        if destination.exists() and not overwrite:
            return self.downloadError, "target file already exists"

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            return self.otherError, "create file error"

        self.last_retries = 0
        for attempt in range(self.max_retries + 1):
            temporary_name = None
            response = None
            try:
                response = self.transport.get(
                    file_url,
                    timeout=self.timeout,
                    stream=True,
                )
                status_code = self._status_code(response)
                if attempt < self.max_retries and self._is_retryable_status(status_code):
                    self.last_retries += 1
                    close = getattr(response, "close", None)
                    if close is not None:
                        close()
                    response = None
                    self._wait_before_retry(self.last_retries)
                    continue
                if not 200 <= status_code < 300:
                    response_content = response.content
                    return self._failure_result(response_content, status_code)

                has_headers = hasattr(response, "headers")
                headers = getattr(response, "headers", {})
                content_type = str(headers.get("Content-Type", "")).lower()
                iterator = getattr(response, "iter_content", None)
                if "json" in content_type or iterator is None or not has_headers:
                    response_content = response.content
                    if self._check_getway_flag(response_content):
                        return self._failure_result(response_content)

                with tempfile.NamedTemporaryFile(
                        mode="wb",
                        dir=destination.parent,
                        prefix=f".{destination.name}.",
                        suffix=".part",
                        delete=False,
                ) as temporary_file:
                    temporary_name = temporary_file.name
                    bytes_written = 0
                    chunks = (
                        iterator(chunk_size=chunk_size)
                        if iterator is not None
                        else (response_content,)
                    )
                    for chunk in chunks:
                        if chunk:
                            temporary_file.write(chunk)
                            bytes_written += len(chunk)
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())

                content_length = getattr(response, "headers", {}).get("Content-Length")
                if content_length is not None and bytes_written != int(content_length):
                    return self.downloadError, "download size does not match Content-Length"
                os.replace(temporary_name, destination)
                temporary_name = None
                return 0, None
            except requests.exceptions.RequestException as error:
                if attempt < self.max_retries and self._is_retryable_exception(error):
                    self.last_retries += 1
                    self._wait_before_retry(self.last_retries)
                    continue
                return self.otherError, "request error"
            except (OSError, ValueError):
                return self.otherError, "create file error"
            finally:
                if temporary_name is not None:
                    try:
                        pathlib.Path(temporary_name).unlink()
                    except FileNotFoundError:
                        pass
                if response is not None:
                    response_close = getattr(response, "close", None)
                    if response_close is not None:
                        response_close()

        return self.otherError, "request error"

    @classmethod
    def generate_pack_failure_handler(
            cls,
            response_data: ResponseData,
    ) -> Callable[[bytes], ResponseData]:
        """Create a compatibility handler for gateway and HTTP failures."""
        def failure_handler(response_content: bytes, status_code: int | None = None) -> ResponseData:
            error_code, error_message = cls._failure_result(response_content, status_code)
            response_data.request.error_code = error_code
            response_data.request.error_message = error_message
            return response_data

        return failure_handler

    @classmethod
    def generate_exception_handler(
            cls,
            response_data: ResponseData,
    ) -> Callable[[Exception], ResponseData]:
        def handle_exception(error: Exception):
            logger.warning(f"Error retrieving data: {type(error).__name__}")
            response_data.request.error_code = cls.otherError
            response_data.request.error_message = "Error retrieving data"
            response_data.request.cause = error
            return response_data

        return handle_exception

    @classmethod
    def generate_pack_success_handler(
            cls,
            response_data: ResponseData,
    ) -> Callable[[bytes], ResponseData]:
        """Create a handler that maps protobuf failures to a decode error."""
        def handle_success(response_content: bytes) -> ResponseData:
            try:
                response_data.load_from_protobuf_content(response_content)
            except Exception as error:
                response_data.request.error_code = cls.decodeError
                response_data.request.error_message = "response decode failed"
                response_data.request.cause = error
            return response_data

        return handle_success

    @classmethod
    def _check_getway_flag(cls, response_data: bytes) -> bool:
        try:
            response_json = json.loads(response_data)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            return cls.getwayFlag in response_data
        return isinstance(response_json, dict) and response_json.get("flag") == "slb"
