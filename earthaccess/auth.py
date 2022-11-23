import getpass
import os
from netrc import NetrcParseError
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import requests  # type: ignore
from tinynetrc import Netrc

from .daac import DAACS


class SessionWithHeaderRedirection(requests.Session):
    """
    Requests removes auth headers if the redirect happens outside the
    original req domain.
    This is taken from https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
    """

    AUTH_HOST = "urs.earthdata.nasa.gov"

    def __init__(
        self, username: Optional[str] = None, password: Optional[str] = None
    ) -> None:
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

    def __init__(self) -> None:
        # Maybe all these predefined URLs should be in a constants.py file
        self.authenticated = False
        self.tokens: List = []
        self.EDL_GET_TOKENS_URL = "https://urs.earthdata.nasa.gov/api/users/tokens"
        self.EDL_GENERATE_TOKENS_URL = "https://urs.earthdata.nasa.gov/api/users/token"
        self.EDL_REVOKE_TOKEN = "https://urs.earthdata.nasa.gov/api/users/revoke_token"

    def login(self, strategy: str = "interactive", persist: bool = False) -> Any:
        """Authenticate with Earthdata login

        Parameters:

            strategy (String): authentication method.

                    "interactive": (default) enter username and password.

                    "netrc": retrieve username and password from ~/.netrc.

                    "environment": retrieve username and password from $EDL_USERNAME and $EDL_PASSWORD.
            persist (Boolean): will persist credentials in a .netrc file
        Returns:
            an instance of Auth.
        """
        if self.authenticated:
            print("We are already authenticated with NASA EDL")
            return self
        if strategy == "interactive":
            self._interactive(persist)
        if strategy == "netrc":
            self._netrc()
        if strategy == "environment":
            self._environment()
        return self

    def refresh_tokens(self) -> bool:
        """Refresh CMR tokens
        Tokens are used to do authenticated queries on CMR for restricted and early access datastes
        This method renews the tokens to make sure we can query the collections allowed to our EDL user.
        """
        if len(self.tokens) == 0:
            resp_tokens = self._generate_user_token(
                username=self._credentials[0], password=self._credentials[1]
            )
            if resp_tokens.ok:
                self.token = resp_tokens.json()
                self.tokens = [self.token]
                print(
                    f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                )
                return True
            else:
                return False
        if len(self.tokens) == 1:
            resp_tokens = self._generate_user_token(
                username=self._credentials[0], password=self._credentials[1]
            )
            if resp_tokens.ok:
                self.token = resp_tokens.json()
                self.tokens.extend(self.token)
                print(
                    f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                )
                return True
            else:
                return False

        if len(self.tokens) == 2:
            resp_revoked = self._revoke_user_token(self.token["access_token"])
            if resp_revoked:
                resp_tokens = self._generate_user_token(
                    username=self._credentials[0], password=self._credentials[1]
                )
                if resp_tokens.ok:
                    self.token = resp_tokens.json()
                    self.tokens[0] = self.token
                    print(
                        f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                    )
                    return True
                else:
                    print(resp_tokens)
                    return False

        return False

    def get_s3_credentials(
        self, daac: str = "", provider: str = ""
    ) -> Union[Dict[str, str], None]:
        """Gets AWS S3 credentials for a given NASA cloud provider

        Parameters:
            provider: A valid cloud provider, each DAAC has a provider code for their cloud distributions
            daac: the name of a NASA DAAC, i.e. NSIDC or PODAAC

        Rreturns:
            A Python dictionary with the temporary AWS S3 credentials

        """
        auth_url = self._get_cloud_auth_url(daac_shortname=daac, provider=provider)
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
            print(f"Credentials for the cloud provider {daac} are not available")
            return None

    def get_session(self, bearer_token: bool = True) -> SessionWithHeaderRedirection:
        """Returns a new request session instance

        Parameters:
            bearer_token (Boolean): boolean, include bearer token
        Returns:
            subclass SessionWithHeaderRedirection instance with Auth and bearer token headers
        """
        session = SessionWithHeaderRedirection(
            self._credentials[0], self._credentials[1]
        )
        if bearer_token and self.authenticated:
            session.headers.update(
                {"Authorization": f'Bearer {self.token["access_token"]}'}
            )
        return session

    def _interactive(self, presist_credentials: bool = True) -> bool:
        username = input("Enter your Earthdata Login username: ")
        password = getpass.getpass(prompt="Enter your Earthdata password: ")
        authenticated = self._get_credentials(username, password)
        if authenticated is True and presist_credentials is True:
            self._persist_user_credentials(username, password)
        return authenticated

    def _netrc(self) -> bool:
        try:
            my_netrc = Netrc()
        except FileNotFoundError as err:
            print(f"Expects .netrc in {os.path.expanduser('~')}")
            print(err)
            return False
        except NetrcParseError as err:
            print("Unable to parse .netrc")
            print(err)
            return False
        if my_netrc["urs.earthdata.nasa.gov"] is not None:
            username = my_netrc["urs.earthdata.nasa.gov"]["login"]
            password = my_netrc["urs.earthdata.nasa.gov"]["password"]
        else:
            return False
        authenticated = self._get_credentials(username, password)
        return authenticated

    def _environment(self) -> bool:
        username = os.getenv("EDL_USERNAME")
        password = os.getenv("EDL_PASSWORD")
        authenticated = self._get_credentials(username, password)
        return authenticated

    def _get_credentials(
        self, username: Optional[str], password: Optional[str]
    ) -> bool:
        if username is not None and password is not None:
            self._session = SessionWithHeaderRedirection(username, password)
            token_resp = self._get_user_tokens(username, password)

            if not (token_resp.ok):  # type: ignore
                print(
                    f"Authentication with Earthdata Login failed with:\n{token_resp.text}"
                )
                return False
            print("You're now authenticated with NASA Earthdata Login")
            self._credentials = (username, password)
            self.tokens = token_resp.json()
            self.authenticated = True

            if len(self.tokens) == 0:
                self.refresh_tokens()
                print(
                    f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                )
                self.token = self.tokens[0]
            elif len(self.tokens) > 0:
                self.token = self.tokens[0]
                print(
                    f"Using token with expiration date: {self.token['expiration_date']}"
                )

        return self.authenticated

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

    def _revoke_user_token(self, token: str) -> bool:
        session = SessionWithHeaderRedirection(
            self._credentials[0], self._credentials[1]
        )
        auth_resp = session.post(
            self.EDL_REVOKE_TOKEN,
            params={"token": token},
            headers={
                "Accept": "application/json",
            },
            timeout=10,
        )
        return auth_resp.ok

    def _persist_user_credentials(self, username: str, password: str) -> bool:
        # See: https://github.com/sloria/tinynetrc/issues/34
        try:
            netrc_path = Path().home().joinpath(".netrc")
            netrc_path.touch(exist_ok=True)
            os.chmod(netrc_path.absolute(), 0o600)
        except Exception as e:
            print(e)
            return False
        my_netrc = Netrc(str(netrc_path))
        my_netrc["urs.earthdata.nasa.gov"] = {"login": username, "password": password}
        my_netrc.save()
        return True

    def _get_cloud_auth_url(self, daac_shortname: str = "", provider: str = "") -> str:
        for daac in DAACS:
            if (
                daac_shortname == daac["short-name"]
                or provider in daac["cloud-providers"]
                and len(daac["s3-credentials"]) > 0
            ):
                return str(daac["s3-credentials"])
        return ""
