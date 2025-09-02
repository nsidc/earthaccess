import getpass
import importlib.metadata
import logging
import os
import platform
import shutil
from netrc import NetrcParseError
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from urllib.parse import urlparse

import requests  # type: ignore
from tinynetrc import Netrc
from typing_extensions import deprecated

from earthaccess.daac import DAACS
from earthaccess.exceptions import LoginAttemptFailure, LoginStrategyUnavailable
from earthaccess.system import PROD, System

try:
    user_agent = f"earthaccess v{importlib.metadata.version('earthaccess')}"
except importlib.metadata.PackageNotFoundError:
    user_agent = "earthaccess"


logger = logging.getLogger(__name__)


def netrc_path() -> Path:
    """Return the path of the `.netrc` file.

    The path may or may not exist.

    See [the `.netrc` file](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html).

    Returns:
        `Path` of the `NETRC` environment variable, if the value is non-empty;
        otherwise, the path of the platform-specific default location:
        `~/_netrc` on Windows systems, `~/.netrc` on non-Windows systems.
    """
    sys_netrc_name = "_netrc" if platform.system() == "Windows" else ".netrc"
    env_netrc = os.environ.get("NETRC")

    return Path(env_netrc) if env_netrc else Path.home() / sys_netrc_name


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
        self.token: Optional[Mapping[str, str]] = None
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
                    Retrieve either a username and password pair from the
                    `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` environment variables,
                    or an Earthdata login token from the `EARTHDATA_TOKEN` environment
                    variable.
            persist: Will persist username and password credentials in a `.netrc` file.
            system: the EDL endpoint to log in to Earthdata, defaults to PROD

        Returns:
            An instance of Auth.

        Raises:
            LoginAttemptFailure: If the NASA Earthdata Login service rejects
                credentials.
        """
        if system is not None:
            self._set_earthdata_system(system)

        if self.authenticated and (system == self.system):
            logger.debug("We are already authenticated with NASA EDL")
            return self

        if strategy == "interactive":
            self._interactive(persist)
        elif strategy == "netrc":
            self._netrc()
        elif strategy == "environment":
            self._environment()

        return self

    def _set_earthdata_system(self, system: System) -> None:
        self.system = system

        # Maybe all these predefined URLs should be in a constants.py file
        self.EDL_FIND_OR_CREATE_TOKEN_URL = (
            f"https://{self.system.edl_hostname}/api/users/find_or_create_token"
        )

        self._eula_url = (
            f"https://{self.system.edl_hostname}/users/earthaccess/unaccepted_eulas"
        )
        self._apps_url = f"https://{self.system.edl_hostname}/application_search"

    @deprecated("No replacement, as tokens are now refreshed automatically.")
    def refresh_tokens(self) -> bool:
        """Refresh CMR tokens.

        Tokens are used to do authenticated queries on CMR for restricted and early access datasets.
        This method renews the tokens to make sure we can query the collections allowed to our EDL user.
        """
        return self.authenticated

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
        if bearer_token and self.token:
            # This will avoid the use of the netrc after we are logged in
            session.trust_env = False
            session.headers.update(
                {"Authorization": f"Bearer {self.token['access_token']}"}
            )
        return session

    def _interactive(
        self,
        persist_credentials: bool = False,
    ) -> bool:
        username = input("Enter your Earthdata Login username: ")
        password = getpass.getpass(prompt="Enter your Earthdata password: ")
        authenticated = self._get_credentials(username, password, None)
        if authenticated:
            logger.debug("Using user provided credentials for EDL")
            if persist_credentials:
                self._persist_user_credentials(username, password)
        return authenticated

    def _netrc(self) -> bool:
        netrc_loc = netrc_path()

        try:
            my_netrc = Netrc(str(netrc_loc))
        except FileNotFoundError as err:
            raise LoginStrategyUnavailable(f"No .netrc found at {netrc_loc}") from err
        except NetrcParseError as err:
            raise LoginStrategyUnavailable(
                f"Unable to parse .netrc file {netrc_loc}"
            ) from err

        creds = my_netrc[self.system.edl_hostname]
        if creds is None:
            raise LoginStrategyUnavailable(
                f"Earthdata Login hostname {self.system.edl_hostname} not found in .netrc file {netrc_loc}"
            )

        username = creds["login"]
        password = creds["password"]

        if username is None:
            raise LoginStrategyUnavailable(
                f"Username not found in .netrc file {netrc_loc}"
            )
        if password is None:
            raise LoginStrategyUnavailable(
                f"Password not found in .netrc file {netrc_loc}"
            )

        authenticated = self._get_credentials(username, password, None)

        if authenticated:
            logger.debug("Using .netrc file for EDL")

        return authenticated

    def _environment(self) -> bool:
        username = os.getenv("EARTHDATA_USERNAME")
        password = os.getenv("EARTHDATA_PASSWORD")
        token = os.getenv("EARTHDATA_TOKEN")

        if (not username or not password) and not token:
            raise LoginStrategyUnavailable(
                "Either the environment variables EARTHDATA_USERNAME and "
                "EARTHDATA_PASSWORD must both be set, or EARTHDATA_TOKEN must be set for "
                "the 'environment' login strategy."
            )

        logger.debug("Using environment variables for EDL")
        return self._get_credentials(username, password, token)

    def _get_credentials(
        self,
        username: Optional[str],
        password: Optional[str],
        user_token: Optional[str],
    ) -> bool:
        if user_token is not None:
            self.token = {"access_token": user_token}
            self.authenticated = True
        if username is not None and password is not None:
            token_resp = self._find_or_create_token(username, password)

            if not (token_resp.ok):  # type: ignore
                msg = f"Authentication with Earthdata Login failed with:\n{token_resp.text}"
                logger.error(msg)
                raise LoginAttemptFailure(msg)

            logger.info("You're now authenticated with NASA Earthdata Login")
            self.username = username
            self.password = password

            token = token_resp.json()
            logger.debug(
                f"Using token with expiration date: {token['expiration_date']}"
            )
            self.token = token
            self.authenticated = True

        return self.authenticated

    def _find_or_create_token(self, username: str, password: str) -> Any:
        session = SessionWithHeaderRedirection(username, password)
        auth_resp = session.post(
            self.EDL_FIND_OR_CREATE_TOKEN_URL,
            headers={
                "Accept": "application/json",
            },
            timeout=10,
        )
        return auth_resp

    def _persist_user_credentials(self, username: str, password: str) -> bool:
        # See: https://github.com/sloria/tinynetrc/issues/34

        netrc_loc = netrc_path()
        logger.info(f"Persisting credentials to {netrc_loc}")

        try:
            netrc_loc.touch(exist_ok=True)
            netrc_loc.chmod(0o600)
        except Exception as e:
            logger.error(e)
            return False

        my_netrc = Netrc(str(netrc_loc))
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
                f"HTTP.COOKIEJAR={urs_cookies_path}\nHTTP.NETRC={netrc_loc}"
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
