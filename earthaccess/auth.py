import getpass
import importlib.metadata
import logging
import os
import platform
import shutil
from netrc import NetrcParseError
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests  # type: ignore
from tinynetrc import Netrc

from .daac import DAACS
from .system import PROD, System

try:
    user_agent = f"earthaccess v{importlib.metadata.version('earthaccess')}"
except importlib.metadata.PackageNotFoundError:
    user_agent = "earthaccess"


logger = logging.getLogger(__name__)


class SessionWithHeaderRedirection(requests.Session):
    """Requests removes auth headers if the redirect happens outside the
    original req domain.
    """

    AUTH_HOSTS: List[str] = [
        "urs.earthdata.nasa.gov",
        "cumulus.asf.alaska.edu",
        "sentinel1.asf.alaska.edu",
        "datapool.asf.alaska.edu",
    ]

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.headers.update({"User-Agent": user_agent})

        if username and password:
            self.auth = (username, password)

    def rebuild_auth(self, prepared_request: Any, response: Any) -> None:
        """Overrides from the library to keep headers when redirected to or from the NASA auth host."""
        headers = prepared_request.headers
        url = prepared_request.url

        if "Authorization" in headers:
            original_parsed = urlparse(response.request.url)
            redirect_parsed = urlparse(url)
            if (original_parsed.hostname != redirect_parsed.hostname) and (
                redirect_parsed.hostname not in self.AUTH_HOSTS
                or original_parsed.hostname not in self.AUTH_HOSTS
            ):
                logger.debug(
                    f"Deleting Auth Headers: {original_parsed.hostname} -> {redirect_parsed.hostname}"
                )
                del headers["Authorization"]
        return


class Auth(object):
    """Authentication class for operations that require Earthdata login (EDL)."""

    def __init__(self) -> None:
        # Maybe all these predefined URLs should be in a constants.py file
        self.authenticated = False
        self.tokens: List = []
        self._set_earthdata_system(PROD)

    def login(
        self,
        strategy: str = "netrc",
        persist: bool = False,
        system: Optional[System] = None,
    ) -> Any:
        """Authenticate with Earthdata login.

        Parameters:
            strategy:
                The authentication method.

                * **"interactive"**: Enter a username and password.
                * **"netrc"**: (default) Retrieve a username and password from ~/.netrc.
                * **"environment"**:
                    Retrieve a username and password from $EARTHDATA_USERNAME and $EARTHDATA_PASSWORD.
            persist: Will persist credentials in a `.netrc` file.
            system: the EDL endpoint to log in to Earthdata, defaults to PROD

        Returns:
            An instance of Auth.
        """
        if system is not None:
            self._set_earthdata_system(system)

        if self.authenticated and (system == self.system):
            logger.debug("We are already authenticated with NASA EDL")
            return self
        if strategy == "interactive":
            self._interactive(persist)
        if strategy == "netrc":
            self._netrc()
        if strategy == "environment":
            self._environment()

        return self

    def _set_earthdata_system(self, system: System) -> None:
        self.system = system

        # Maybe all these predefined URLs should be in a constants.py file
        self.EDL_GET_TOKENS_URL = f"https://{self.system.edl_hostname}/api/users/tokens"
        self.EDL_GENERATE_TOKENS_URL = (
            f"https://{self.system.edl_hostname}/api/users/token"
        )
        self.EDL_REVOKE_TOKEN = (
            f"https://{self.system.edl_hostname}/api/users/revoke_token"
        )

        self._eula_url = (
            f"https://{self.system.edl_hostname}/users/earthaccess/unaccepted_eulas"
        )
        self._apps_url = f"https://{self.system.edl_hostname}/application_search"

    def refresh_tokens(self) -> bool:
        """Refresh CMR tokens.

        Tokens are used to do authenticated queries on CMR for restricted and early access datasets.
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
                    logger.info(resp_tokens)
                    return False

        return False

    def get_s3_credentials(
        self,
        daac: Optional[str] = None,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Dict[str, str]:
        """Gets AWS S3 credentials for a given NASA cloud provider.

        The easier way is to use the DAAC short name; provider is optional if we know it.

        Parameters:
            daac: The name of a NASA DAAC, e.g. NSIDC or PODAAC.
            provider: A valid cloud provider. Each DAAC has a provider code for their cloud distributions.
            endpoint: Getting the credentials directly from the S3Credentials URL.

        Returns:
            A Python dictionary with the temporary AWS S3 credentials.
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
                        logger.error(
                            f"Authentication with Earthdata Login failed with:\n{auth_resp.text[0:1000]}"
                        )
                        logger.error(
                            f"Consider accepting the EULAs available at {self._eula_url} and applications at {self._apps_url}"
                        )
                        return {}

                    return auth_resp.json()
                return auth_resp.json()
            else:
                # This happens if the cloud provider doesn't list the S3 credentials or the DAAC
                # does not have cloud collections yet
                logger.info(
                    f"Credentials for the cloud provider {daac} are not available"
                )
                return {}
        else:
            logger.info("We need to authenticate with EDL first")
            return {}

    def get_session(self, bearer_token: bool = True) -> requests.Session:
        """Returns a new request session instance.

        Parameters:
            bearer_token: whether to include bearer token

        Returns:
            class Session instance with Auth and bearer token headers
        """
        session = SessionWithHeaderRedirection()
        if bearer_token and self.authenticated:
            # This will avoid the use of the netrc after we are logged in
            session.trust_env = False
            session.headers.update(
                {"Authorization": f'Bearer {self.token["access_token"]}'}
            )
        return session

    def _interactive(self, persist_credentials: bool = False) -> bool:
        username = input("Enter your Earthdata Login username: ")
        password = getpass.getpass(prompt="Enter your Earthdata password: ")
        authenticated = self._get_credentials(username, password)
        if authenticated:
            logger.debug("Using user provided credentials for EDL")
            if persist_credentials:
                logger.info("Persisting credentials to .netrc")
                self._persist_user_credentials(username, password)
        return authenticated

    def _netrc(self) -> bool:
        try:
            my_netrc = Netrc()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"No .netrc found in {Path.home()}") from err
        except NetrcParseError as err:
            raise NetrcParseError("Unable to parse .netrc") from err
        if (creds := my_netrc[self.system.edl_hostname]) is None:
            return False

        username = creds["login"]
        password = creds["password"]
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
                logger.info(
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
            netrc_path.chmod(0o600)
        except Exception as e:
            logger.error(e)
            return False
        my_netrc = Netrc(str(netrc_path))
        my_netrc[self.system.edl_hostname] = {
            "login": username,
            "password": password,
        }
        my_netrc.save()
        urs_cookies_path = Path.home() / ".urs_cookies"
        if not urs_cookies_path.exists():
            urs_cookies_path.write_text("")

        # Create and write to .dodsrc file
        dodsrc_path = Path.home() / ".dodsrc"
        if not dodsrc_path.exists():
            dodsrc_contents = (
                f"HTTP.COOKIEJAR={urs_cookies_path}\nHTTP.NETRC={netrc_path}"
            )
            dodsrc_path.write_text(dodsrc_contents)

        if platform.system() == "Windows":
            local_dodsrc_path = Path.cwd() / dodsrc_path.name
            if not local_dodsrc_path.exists():
                shutil.copy2(dodsrc_path, local_dodsrc_path)

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
