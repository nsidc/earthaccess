from copy import deepcopy
from typing import Any, Dict

from pydantic import BaseModel
from requests import exceptions, session
from requests.auth import HTTPBasicAuth


class Auth(BaseModel):
    """
    some data
    """

    def __init__(self, username: str, password: str):
        EDL_TOKEN_URL = "https://cmr.earthdata.nasa.gov/legacy-services/rest/tokens"
        self.session = session()

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
            self.token = auth_resp.json()["token"]["id"]

    def get_session(self) -> session:
        return deepcopy(self.session)

    def get_s3_credentials(
        self, auth_url="https://data.nsidc.earthdatacloud.nasa.gov/s3credentials"
    ) -> Dict(str, str):

        cumulus_resp = self.session.get(auth_url, timeout=10, allow_redirects=True)
        auth_resp = self.session.get(
            cumulus_resp.url, auth=self.auth, allow_redirects=True, timeout=10
        )
        if not (auth_resp.ok):  # type: ignore
            print(f"Authentication with Earthdata Login failed with:\n{auth_resp.text}")
            return None
        return auth_resp.json()
