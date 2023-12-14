"""Flipkart Authentication."""

from __future__ import annotations

from singer_sdk.authenticators import OAuthAuthenticator, SingletonMeta
import base64

from singer_sdk.helpers._util import utc_now
import requests


class FlipkartAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    """Authenticator class for Flipkart."""

    @property
    def oauth_request_body(self) -> dict:
        """Define the OAuth request body for the AutomaticTestTap API.

        Returns:
            A dict with the request body
        """
        return {}

    @classmethod
    def create_for_stream(
        cls,
        stream,
    ) -> FlipkartAuthenticator:  # noqa: ANN001
        """Instantiate an authenticator for a specific Singer stream.

        Args:
            stream: The Singer stream instance.

        Returns:
            A new authenticator.
        """
        return cls(
            stream=stream,
            auth_endpoint="https://api.flipkart.net/oauth-service/oauth/token",
            # oauth_headers={"Authorization": f"Basic {auth_token}"}
        )

    # @property
    # def auth_params(self) -> dict:
    #     """Get query parameters.

    #     Returns:
    #         URL query parameters for authentication.
    #     """
    #     return {"grant_type": "client_credentials", "scope": "Seller_Api"}

    def update_access_token(self) -> None:
        """Update `access_token` along with: `last_refreshed` and `expires_in`.

        Raises:
            RuntimeError: When OAuth login fails.
        """
        request_time = utc_now()
        # url = "https://api.flipkart.net/oauth-service/oauth/token"
        querystring = {"grant_type": "client_credentials", "scope": "Seller_Api"}

        credentials = f"{self.client_id}:{self.client_secret}".encode()
        auth_token = base64.b64encode(credentials).decode("ascii")
        headers = {"Authorization": f"Basic {auth_token}"}
        token_response = requests.get(
            self.auth_endpoint,
            headers=headers,
            params=querystring,
            timeout=60,
        )

        try:
            token_response.raise_for_status()
        except requests.HTTPError as ex:
            msg = f"Failed OAuth login, response was '{token_response.json()}'. {ex}"
            raise RuntimeError(msg) from ex

        self.logger.info("OAuth authorization attempt was successful.")

        token_json = token_response.json()
        self.access_token = token_json["access_token"]
        expiration = token_json.get("expires_in", self._default_expiration)
        self.expires_in = int(expiration) if expiration else None
        if self.expires_in is None:
            self.logger.debug(
                "No expires_in received in OAuth response and no "
                "default_expiration set. Token will be treated as if it never "
                "expires.",
            )
        self.last_refreshed = request_time