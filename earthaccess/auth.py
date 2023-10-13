import getpass
import logging
import os
from netrc import NetrcParseError
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests  # type: ignore
from tinynetrc import Netrc

from .daac import DAACS

logger = logging.getLogger(__name__)


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
        self.EDL_GET_PROFILE = "https://urs.earthdata.nasa.gov/api/users/<USERNAME>?client_id=ntD0YGC_SM3Bjs-Tnxd7bg"
        self.EDL_GENERATE_TOKENS_URL = "https://urs.earthdata.nasa.gov/api/users/token"
        self.EDL_REVOKE_TOKEN = "https://urs.earthdata.nasa.gov/api/users/revoke_token"

    def login(self, strategy: str = "netrc", persist: bool = False) -> Any:
        """Authenticate with Earthdata login

        Parameters:

            strategy (String): authentication method.

                    "interactive": enter username and password.

                    "netrc": (default) retrieve username and password from ~/.netrc.

                    "environment": retrieve username and password from $EARTHDATA_USERNAME and $EARTHDATA_PASSWORD.
            persist (Boolean): will persist credentials in a .netrc file
        Returns:
            an instance of Auth.
        """
        if self.authenticated:
            logger.debug("We are already authenticated with NASA EDL")
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
                username=self.username, password=self.password
            )
            if resp_tokens.ok:
                self.token = resp_tokens.json()
                self.tokens = [self.token]
                logger.debug(
                    f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                )
                return True
            else:
                return False
        if len(self.tokens) == 1:
            resp_tokens = self._generate_user_token(
                username=self.username, password=self.password
            )
            if resp_tokens.ok:
                self.token = resp_tokens.json()
                self.tokens.extend(self.token)
                logger.debug(
                    f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                )
                return True
            else:
                return False

        if len(self.tokens) == 2:
            resp_revoked = self._revoke_user_token(self.token["access_token"])
            if resp_revoked:
                resp_tokens = self._generate_user_token(
                    username=self.username, password=self.password
                )
                if resp_tokens.ok:
                    self.token = resp_tokens.json()
                    self.tokens[0] = self.token
                    logger.debug(
                        f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                    )
                    return True
                else:
                    print(resp_tokens)
                    return False

        return False

    def get_s3_credentials(
        self,
        daac: Optional[str] = None,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Dict[str, str]:
        """Gets AWS S3 credentials for a given NASA cloud provider, the
        easier way is to use the DAAC short name. provider is optional if we know it.

        Parameters:
            provider: A valid cloud provider, each DAAC has a provider code for their cloud distributions
            daac: the name of a NASA DAAC, i.e. NSIDC or PODAAC
            endpoint: getting the credentials directly from the S3Credentials URL

        Rreturns:
            A Python dictionary with the temporary AWS S3 credentials

        """
        if self.authenticated:
            session = SessionWithHeaderRedirection(self.username, self.password)
            if endpoint is None:
                auth_url = self._get_cloud_auth_url(
                    daac_shortname=daac, provider=provider
                )
            else:
                auth_url = endpoint
            if auth_url.startswith("https://"):
                cumulus_resp = session.get(auth_url, timeout=15, allow_redirects=True)
                auth_resp = session.get(
                    cumulus_resp.url, allow_redirects=True, timeout=15
                )
                if not (auth_resp.ok):  # type: ignore
                    # Let's try to authenticate with Bearer tokens
                    _session = self.get_session()
                    cumulus_resp = _session.get(
                        auth_url, timeout=15, allow_redirects=True
                    )
                    auth_resp = _session.get(
                        cumulus_resp.url, allow_redirects=True, timeout=15
                    )
                    if not (auth_resp.ok):
                        print(
                            f"Authentication with Earthdata Login failed with:\n{auth_resp.text[0:1000]}"
                        )
                        eula_url = "https://urs.earthdata.nasa.gov/users/earthaccess/unaccepted_eulas"
                        apps_url = "https://urs.earthdata.nasa.gov/application_search"
                        print(
                            f"Consider accepting the EULAs available at {eula_url} and applications at {apps_url}"
                        )
                        return {}

                    return auth_resp.json()
                return auth_resp.json()
            else:
                # This happens if the cloud provider doesn't list the S3 credentials or the DAAC
                # does not have cloud collections yet
                print(f"Credentials for the cloud provider {daac} are not available")
                return {}
        else:
            print("We need to auhtenticate with EDL first")
            return {}

    def get_session(self, bearer_token: bool = True) -> requests.Session:
        """Returns a new request session instance

        Parameters:
            bearer_token (Boolean): boolean, include bearer token
        Returns:
            class Session instance with Auth and bearer token headers
        """
        session = requests.Session()
        if bearer_token and self.authenticated:
            # This will avoid the use of the netrc after we are logged in
            session.trust_env = False
            session.headers.update(
                {"Authorization": f'Bearer {self.token["access_token"]}'}
            )
        return session

    def get_user_profile(self) -> Dict[str, Any]:
        if hasattr(self, "username") and self.authenticated:
            session = self.get_session()
            url = self.EDL_GET_PROFILE.replace("<USERNAME>", self.username)
            user_profile = session.get(url).json()
            return user_profile
        else:
            return {}

    def _interactive(self, presist_credentials: bool = False) -> bool:
        username = input("Enter your Earthdata Login username: ")
        password = getpass.getpass(prompt="Enter your Earthdata password: ")
        authenticated = self._get_credentials(username, password)
        if authenticated:
            logger.debug("Using user provided credentials for EDL")
            if presist_credentials:
                print("Persisting credentials to .netrc")
                self._persist_user_credentials(username, password)
        return authenticated

    def _netrc(self) -> bool:
        try:
            my_netrc = Netrc()
        except FileNotFoundError as err:
            raise FileNotFoundError(
                f"No .netrc found in {os.path.expanduser('~')}"
            ) from err
        except NetrcParseError as err:
            raise NetrcParseError("Unable to parse .netrc") from err
        if my_netrc["urs.earthdata.nasa.gov"] is not None:
            username = my_netrc["urs.earthdata.nasa.gov"]["login"]
            password = my_netrc["urs.earthdata.nasa.gov"]["password"]
        else:
            return False
        authenticated = self._get_credentials(username, password)
        if authenticated:
            logger.debug("Using .netrc file for EDL")
        return authenticated

    def _environment(self) -> bool:
        username = os.getenv("EARTHDATA_USERNAME")
        password = os.getenv("EARTHDATA_PASSWORD")
        authenticated = self._get_credentials(username, password)
        if authenticated:
            logger.debug("Using environment variables for EDL")
        else:
            logger.debug(
                "EARTHDATA_USERNAME and EARTHDATA_PASSWORD are not set in the current environment, try "
                "setting them or use a different strategy (netrc, interactive)"
            )
        return authenticated

    def _get_credentials(
        self, username: Optional[str], password: Optional[str]
    ) -> bool:
        if username is not None and password is not None:
            token_resp = self._get_user_tokens(username, password)

            if not (token_resp.ok):  # type: ignore
                print(
                    f"Authentication with Earthdata Login failed with:\n{token_resp.text}"
                )
                return False
            logger.debug("You're now authenticated with NASA Earthdata Login")
            self.username = username
            self.password = password

            self.tokens = token_resp.json()
            self.authenticated = True

            if len(self.tokens) == 0:
                self.refresh_tokens()
                logger.debug(
                    f"earthaccess generated a token for CMR with expiration on: {self.token['expiration_date']}"
                )
                self.token = self.tokens[0]
            elif len(self.tokens) > 0:
                self.token = self.tokens[0]
                logger.debug(
                    f"Using token with expiration date: {self.token['expiration_date']}"
                )
            profile = self.get_user_profile()
            if "email_address" in profile:
                self.user_profile = profile
                self.email = profile["email_address"]
            else:
                self.email = ""

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
        if self.authenticated:
            session = SessionWithHeaderRedirection(self.username, self.password)
            auth_resp = session.post(
                self.EDL_REVOKE_TOKEN,
                params={"token": token},
                headers={
                    "Accept": "application/json",
                },
                timeout=10,
            )
            return auth_resp.ok
        else:
            return False

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

    def _get_cloud_auth_url(
        self, daac_shortname: Optional[str] = "", provider: Optional[str] = ""
    ) -> str:
        for daac in DAACS:
            if (
                daac_shortname == daac["short-name"]
                or provider in daac["cloud-providers"]
                and len(daac["s3-credentials"]) > 0
            ):
                return str(daac["s3-credentials"])
        return ""
