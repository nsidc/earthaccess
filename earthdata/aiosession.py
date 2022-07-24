import asyncio
from contextlib import suppress
from types import SimpleNamespace
from typing import (Any, Awaitable, Callable, Iterable, Mapping, Optional,
                    Type, Union)

import aiohttp
from aiohttp import ClientSession, ClientTimeout, hdrs, payload
from aiohttp.client_exceptions import ClientError as ClientError
from aiohttp.client_exceptions import ClientOSError as ClientOSError
from aiohttp.client_exceptions import InvalidURL as InvalidURL
from aiohttp.client_exceptions import ServerTimeoutError as ServerTimeoutError
from aiohttp.client_exceptions import TooManyRedirects as TooManyRedirects
from aiohttp.client_reqrep import SSL_ALLOWED_TYPES as SSL_ALLOWED_TYPES
from aiohttp.client_reqrep import ClientResponse as ClientResponse
from aiohttp.client_reqrep import Fingerprint as Fingerprint
from aiohttp.cookiejar import CookieJar
from aiohttp.helpers import (_SENTINEL, BasicAuth, TimeoutHandle, ceil_timeout,
                             get_env_proxy_for_url, sentinel,
                             strip_auth_from_url)
from aiohttp.tracing import Trace
from aiohttp.typedefs import LooseCookies, LooseHeaders, StrOrURL
from multidict import istr
from yarl import URL

try:
    from ssl import SSLContext
except ImportError:  # pragma: no cover
    SSLContext = object  # type: ignore[misc,assignment]


class AioSession(aiohttp.ClientSession):
    def __init_subclass__(cls: Type["ClientSession"]) -> None:
        pass

    async def _request(
        self,
        method: str,
        str_or_url: StrOrURL,
        *,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        cookies: Optional[LooseCookies] = None,
        headers: Optional[LooseHeaders] = None,
        skip_auto_headers: Optional[Iterable[str]] = None,
        auth: Optional[BasicAuth] = None,
        allow_redirects: bool = True,
        max_redirects: int = 10,
        compress: Optional[str] = None,
        chunked: Optional[bool] = None,
        expect100: bool = False,
        raise_for_status: Union[
            None, bool, Callable[[ClientResponse], Awaitable[None]]
        ] = None,
        read_until_eof: bool = True,
        proxy: Optional[StrOrURL] = None,
        proxy_auth: Optional[BasicAuth] = None,
        timeout: Union[ClientTimeout, _SENTINEL, None] = sentinel,
        ssl: Optional[Union[SSLContext, bool, Fingerprint]] = None,
        proxy_headers: Optional[LooseHeaders] = None,
        trace_request_ctx: Optional[SimpleNamespace] = None,
        read_bufsize: Optional[int] = None,
    ) -> ClientResponse:

        # NOTE: timeout clamps existing connect and read timeouts.  We cannot
        # set the default to None because we need to detect if the user wants
        # to use the existing timeouts by setting timeout to None.

        if self.closed:
            raise RuntimeError("Session is closed")

        if not isinstance(ssl, SSL_ALLOWED_TYPES):
            raise TypeError(
                "ssl should be SSLContext, bool, Fingerprint, "
                "or None, got {!r} instead.".format(ssl)
            )

        if data is not None and json is not None:
            raise ValueError(
                "data and json parameters can not be used at the same time"
            )
        elif json is not None:
            data = payload.JsonPayload(json, dumps=self._json_serialize)

        redirects = 0
        history = []
        version = self._version

        # Merge with default headers and transform to CIMultiDict
        headers = self._prepare_headers(headers)
        proxy_headers = self._prepare_headers(proxy_headers)

        try:
            url = self._build_url(str_or_url)
        except ValueError as e:
            raise InvalidURL(str_or_url) from e

        skip_headers = set(self._skip_auto_headers)
        if skip_auto_headers is not None:
            for i in skip_auto_headers:
                skip_headers.add(istr(i))

        if proxy is not None:
            try:
                proxy = URL(proxy)
            except ValueError as e:
                raise InvalidURL(proxy) from e

        if timeout is sentinel or timeout is None:
            real_timeout: ClientTimeout = self._timeout
        else:
            real_timeout = timeout
        # timeout is cumulative for all request operations
        # (request, redirects, responses, data consuming)
        tm = TimeoutHandle(
            self._loop, real_timeout.total, ceil_threshold=real_timeout.ceil_threshold
        )
        handle = tm.start()

        if read_bufsize is None:
            read_bufsize = self._read_bufsize

        traces = [
            Trace(
                self,
                trace_config,
                trace_config.trace_config_ctx(trace_request_ctx=trace_request_ctx),
            )
            for trace_config in self._trace_configs
        ]

        for trace in traces:
            await trace.send_request_start(method, url.update_query(params), headers)

        timer = tm.timer()
        try:
            with timer:
                while True:
                    url, auth_from_url = strip_auth_from_url(url)
                    if auth and auth_from_url:
                        raise ValueError(
                            "Cannot combine AUTH argument with "
                            "credentials encoded in URL"
                        )

                    if auth is None:
                        auth = auth_from_url
                    if auth is None:
                        auth = self._default_auth
                    # It would be confusing if we support explicit
                    # Authorization header with auth argument
                    if (
                        headers is not None
                        and auth is not None
                        and hdrs.AUTHORIZATION in headers
                    ):
                        raise ValueError(
                            "Cannot combine AUTHORIZATION header "
                            "with AUTH argument or credentials "
                            "encoded in URL"
                        )

                    all_cookies = self._cookie_jar.filter_cookies(url)

                    if cookies is not None:
                        tmp_cookie_jar = CookieJar()
                        tmp_cookie_jar.update_cookies(cookies)
                        req_cookies = tmp_cookie_jar.filter_cookies(url)
                        if req_cookies:
                            all_cookies.load(req_cookies)

                    if proxy is not None:
                        proxy = URL(proxy)
                    elif self._trust_env:
                        with suppress(LookupError):
                            proxy, proxy_auth = get_env_proxy_for_url(url)

                    req = self._request_class(
                        method,
                        url,
                        params=params,
                        headers=headers,
                        skip_auto_headers=skip_headers,
                        data=data,
                        cookies=all_cookies,
                        auth=auth,
                        version=version,
                        compress=compress,
                        chunked=chunked,
                        expect100=expect100,
                        loop=self._loop,
                        response_class=self._response_class,
                        proxy=proxy,
                        proxy_auth=proxy_auth,
                        timer=timer,
                        session=self,
                        ssl=ssl,
                        proxy_headers=proxy_headers,
                        traces=traces,
                    )

                    # connection timeout
                    try:
                        async with ceil_timeout(
                            real_timeout.connect,
                            ceil_threshold=real_timeout.ceil_threshold,
                        ):
                            assert self._connector is not None
                            conn = await self._connector.connect(
                                req, traces=traces, timeout=real_timeout
                            )
                    except asyncio.TimeoutError as exc:
                        raise ServerTimeoutError(
                            f"Connection timeout to host {url}"
                        ) from exc

                    assert conn.transport is not None

                    assert conn.protocol is not None
                    conn.protocol.set_response_params(
                        timer=timer,
                        skip_payload=method.upper() == "HEAD",
                        read_until_eof=read_until_eof,
                        auto_decompress=self._auto_decompress,
                        read_timeout=real_timeout.sock_read,
                        read_bufsize=read_bufsize,
                        timeout_ceil_threshold=self._connector._timeout_ceil_threshold,
                    )

                    try:
                        try:
                            resp = await req.send(conn)
                            try:
                                await resp.start(conn)
                            except BaseException:
                                resp.close()
                                raise
                        except BaseException:
                            conn.close()
                            raise
                    except ClientError:
                        raise
                    except OSError as exc:
                        raise ClientOSError(*exc.args) from exc

                    self._cookie_jar.update_cookies(resp.cookies, resp.url)

                    # redirects
                    if resp.status in (301, 302, 303, 307, 308) and allow_redirects:

                        for trace in traces:
                            await trace.send_request_redirect(
                                method, url.update_query(params), headers, resp
                            )

                        redirects += 1
                        history.append(resp)
                        if max_redirects and redirects >= max_redirects:
                            resp.close()
                            raise TooManyRedirects(
                                history[0].request_info, tuple(history)
                            )

                        # For 301 and 302, mimic IE, now changed in RFC
                        # https://github.com/kennethreitz/requests/pull/269
                        if (resp.status == 303 and resp.method != hdrs.METH_HEAD) or (
                            resp.status in (301, 302) and resp.method == hdrs.METH_POST
                        ):
                            method = hdrs.METH_GET
                            data = None
                            if headers.get(hdrs.CONTENT_LENGTH):
                                headers.pop(hdrs.CONTENT_LENGTH)

                        r_url = resp.headers.get(hdrs.LOCATION) or resp.headers.get(
                            hdrs.URI
                        )
                        if r_url is None:
                            # see github.com/aio-libs/aiohttp/issues/2022
                            break
                        else:
                            # reading from correct redirection
                            # response is forbidden
                            resp.release()

                        try:
                            parsed_url = URL(
                                r_url, encoded=not self._requote_redirect_url
                            )

                        except ValueError as e:
                            raise InvalidURL(r_url) from e

                        scheme = parsed_url.scheme
                        if scheme not in ("http", "https", ""):
                            resp.close()
                            raise ValueError("Can redirect only to http or https")
                        elif not scheme:
                            parsed_url = url.join(parsed_url)

                        is_same_host_https_redirect = (
                            url.host == parsed_url.host
                            and parsed_url.scheme == "https"
                            and url.scheme == "http"
                        )

                        if (
                            url.origin() != parsed_url.origin()
                            and not is_same_host_https_redirect
                            and "urs.earthdata.nasa.gov" not in parsed_url.origin()
                        ):
                            print(url, parsed_url)
                            auth = None
                            headers.pop(hdrs.AUTHORIZATION, None)

                        url = parsed_url
                        params = None
                        resp.release()
                        continue

                    break

            # check response status
            if raise_for_status is None:
                raise_for_status = self._raise_for_status

            if raise_for_status is None:
                pass
            elif callable(raise_for_status):
                await raise_for_status(resp)
            elif raise_for_status:
                resp.raise_for_status()

            # register connection
            if handle is not None:
                if resp.connection is not None:
                    resp.connection.add_callback(handle.cancel)
                else:
                    handle.cancel()

            resp._history = tuple(history)

            for trace in traces:
                await trace.send_request_end(
                    method, url.update_query(params), headers, resp
                )
            return resp

        except BaseException as e:
            # cleanup timer
            tm.close()
            if handle:
                handle.cancel()
                handle = None

            for trace in traces:
                await trace.send_request_exception(
                    method, url.update_query(params), headers, e
                )
            raise
