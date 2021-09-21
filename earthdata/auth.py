import getpass
from typing import Any, Dict, Union

from requests import session
from requests.auth import HTTPBasicAuth

from .daac import DAACS


class Auth(object):
    """
    Authentication class for operations that require Earthdata login (EDL)
    """

    def __init__(self) -> None:
        # TODO: This token will be deprecated soon, we need to reimplement bearer token.
        # Maybe all these predefined URLs should be in a constants.py file
        EDL_TOKEN_URL = "https://cmr.earthdata.nasa.gov/legacy-services/rest/tokens"
        # EDL_TOKEN_URL = "https://urs.earthdata.nasa.gov/api/users/tokens"
        self.session = session()

        username = input("Enter your Earthdata Login username: ")
        password = getpass.getpass(prompt="Enter your Earthdata password: ")

        if username is not None and password is not None:
            _TOKEN_DATA = (
                "<token>"
                "<username>%s</username>"
                "<password>%s</password>"
                "<client_id>CMR Client</client_id>"
                "<user_ip_address>%s</user_ip_address>"
                "</token>"
            )
            my_ip = self.session.get("https://ipinfo.io/ip").text.strip()
            self.auth = HTTPBasicAuth(username, password)
            # This token is valid for up to 3 months after is issued.
            # It's used to make authenticated calls to CMR to get back private collections
            auth_resp = self.session.post(
                EDL_TOKEN_URL,
                auth=self.auth,
                data=_TOKEN_DATA % (str(username), str(password), my_ip),
                headers={
                    "Content-Type": "application/xml",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            if not (auth_resp.ok):  # type: ignore
                print(
                    f"Authentication with Earthdata Login failed with:\n{auth_resp.text}"
                )
                self.authenticated = False
                return
            print("You're now authenticated with NASA Earthdata Login")
            self.authenticated = True
            self.token = auth_resp.json()["token"]["id"]

    def _get_session(self) -> Any:
        return self.session

    def _get_cloud_auth_url(self, cloud_provider: str = "") -> str:
        for provider in DAACS:
            if (
                cloud_provider in provider["cloud-providers"]
                and len(provider["s3-credentials"]) > 0
            ):
                return str(provider["s3-credentials"])
        return ""

    def get_s3_credentials(
        self, cloud_provider: str = ""
    ) -> Union[Dict[str, str], None]:
        auth_url = self._get_cloud_auth_url(cloud_provider)
        if auth_url.startswith("https://"):
            cumulus_resp = self.session.get(auth_url, timeout=10, allow_redirects=True)
            auth_resp = self.session.get(
                cumulus_resp.url, auth=self.auth, allow_redirects=True, timeout=10
            )
            if not (auth_resp.ok):  # type: ignore
                print(
                    f"Authentication with Earthdata Login failed with:\n{auth_resp.text}"
                )
                return None
            return auth_resp.json()
        else:
            print("We can only get credentials using a valid HTTPS endpoint")
            return None
