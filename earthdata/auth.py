import getpass
from typing import Any, Dict, Union
from urllib.parse import urlparse

import requests  # type: ignore

from .daac import DAACS


class SessionWithHeaderRedirection(requests.Session):
    """
    Requests removes auth headers if the redirect happens outside the
    original req domain. This is taken from https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
    """

    AUTH_HOST = "urs.earthdata.nasa.gov"

    def __init__(self, username: str = None, password: str = None) -> None:
        super().__init__()
        if username and password:
            self.auth = (username, password)

    # Overrides from the library to keep headers when redirected to or from
    # the NASA auth host.
    def rebuild_auth(self, prepared_request: Any, response: Any) -> None:
        headers = prepared_request.headers
        url = prepared_request.url

        if "Authorization" in headers:

            original_parsed = urlparse(response.request.url)
            redirect_parsed = urlparse(url)
            if (
                (original_parsed.hostname != redirect_parsed.hostname)
                and redirect_parsed.hostname != self.AUTH_HOST
                and original_parsed.hostname != self.AUTH_HOST
            ):

                del headers["Authorization"]
        return


class Auth(object):
    """
    Authentication class for operations that require Earthdata login (EDL)
    """

    def _get_user_tokens(self, username: str, password: str) -> Any:
        session = SessionWithHeaderRedirection(username, password)
        auth_resp = session.get(
            self.EDL_GET_TOKENS_URL,
            headers={
                "Accept": "application/json",
            },
            timeout=10,
        )
        return auth_resp

    def _generate_user_token(self, username: str, password: str) -> Any:
        session = SessionWithHeaderRedirection(username, password)
        auth_resp = session.post(
            self.EDL_GENERATE_TOKENS_URL,
            headers={
                "Accept": "application/json",
            },
            timeout=10,
        )
        return auth_resp

    def __init__(self) -> None:
        # Maybe all these predefined URLs should be in a constants.py file

        self.EDL_GET_TOKENS_URL = "https://urs.earthdata.nasa.gov/api/users/tokens"
        self.EDL_GENERATE_TOKENS_URL = "https://urs.earthdata.nasa.gov/api/users/token"

        username = input("Enter your Earthdata Login username: ")
        password = getpass.getpass(prompt="Enter your Earthdata password: ")

        if username is not None and password is not None:
            self._session = SessionWithHeaderRedirection(username, password)
            token_resp = self._get_user_tokens(username, password)

            if not (token_resp.ok):  # type: ignore
                print(
                    f"Authentication with Earthdata Login failed with:\n{token_resp.text}"
                )
                self.authenticated = False
                return
            print("You're now authenticated with NASA Earthdata Login")
            self._credentials = (username, password)
            self.authenticated = True
            tokens = token_resp.json()
            if len(tokens) > 0:
                self.token = tokens[0]
            else:
                try:
                    resp_tokens = self._generate_user_token(username, password)
                    self.token = resp_tokens.json()[0]
                except Exception:
                    print(resp_tokens.text)
                    self.token = None

    def _get_cloud_auth_url(self, cloud_provider: str = "") -> str:
        for provider in DAACS:
            if (
                cloud_provider in provider["cloud-providers"]
                and len(provider["s3-credentials"]) > 0
            ):
                return str(provider["s3-credentials"])
        return ""

    def get_session(self, bearer_token: bool = False) -> Any:
        """
        returns a new request session instance, since looks like using a session in a context is not threadsafe
        https://github.com/psf/requests/issues/1871
        Session with bearer tokens are used by CMR, simple auth sessions can be used do download data
        from on-prem DAAC data centers.
        :returns: subclass SessionWithHeaderRedirection instance
        """
        if bearer_token and self.authenticated:
            session = SessionWithHeaderRedirection()
            session.headers.update(
                {"Authorization": f'Bearer {self.token["access_token"]}'}
            )
            return session
        else:
            return SessionWithHeaderRedirection(
                self._credentials[0], self._credentials[1]
            )

    def get_s3_credentials(
        self, cloud_provider: str = ""
    ) -> Union[Dict[str, str], None]:
        """
        gets AWS S3 credentials for a given NASA cloud provider
        :param cloud_provider: a NASA DAAC cloud provider i.e. POCLOUD
        :returns: a python dictionary with the S3 keys or None
        """
        auth_url = self._get_cloud_auth_url(cloud_provider)
        if auth_url.startswith("https://"):
            cumulus_resp = self._session.get(auth_url, timeout=10, allow_redirects=True)
            auth_resp = self._session.get(
                cumulus_resp.url, allow_redirects=True, timeout=10
            )
            if not (auth_resp.ok):  # type: ignore
                print(
                    f"Authentication with Earthdata Login failed with:\n{auth_resp.text}"
                )
                return None
            return auth_resp.json()
        else:
            # This happens if the cloud provider doesn't list the S3 credentials or the DAAC
            # does not have cloud collections yet
            print(
                f"Credentials for the cloud provider {cloud_provider} are not available"
            )
            return None
