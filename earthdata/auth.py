from copy import deepcopy
from getpass import getpass
from typing import Any, Dict, Union

from requests import session
from requests.auth import HTTPBasicAuth


class Auth(object):
    """
    Auth object for EDL operations
    """

    def __init__(self) -> None:
        EDL_TOKEN_URL = "https://cmr.earthdata.nasa.gov/legacy-services/rest/tokens"
        # TODO: This token will be deprecated soon, we need to reimplement bearer token.
        # EDL_BEARER_TOKEN_URL = "https://urs.earthdata.nasa.gov/generate_token"
        self.session = session()

        username = input("Enter your Earthdata Login username: ")
        password = getpass(prompt="Enter your Earthdata password: ")

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
                return None
            print("You're now authenticated with NASA Earthdata Login")
            self.token = auth_resp.json()["token"]["id"]

    def get_session(self) -> Any:
        return deepcopy(self.session)

    def get_s3_credentials(
        self, auth_url: str = "https://data.nsidc.earthdatacloud.nasa.gov/s3credentials"
    ) -> Union[Dict[str, str], None]:

        cumulus_resp = self.session.get(auth_url, timeout=10, allow_redirects=True)
        auth_resp = self.session.get(
            cumulus_resp.url, auth=self.auth, allow_redirects=True, timeout=10
        )
        if not (auth_resp.ok):  # type: ignore
            print(f"Authentication with Earthdata Login failed with:\n{auth_resp.text}")
            return None
        return auth_resp.json()
