"""REST client handling, including FlipkartStream base class."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
from tap_flipkart.auth import FlipkartAuthenticator

import requests
from singer_sdk.pagination import BaseAPIPaginator  # noqa: TCH002
from singer_sdk.streams import RESTStream

# from tap_flipkart.auth import FlipkartAuthenticator
from tap_flipkart.paginator import FlipkartPaginator

_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class FlipkartStream(RESTStream):
    """Flipkart stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return "https://api.flipkart.net/sellers"
    

    records_jsonpath = "$[*]"  # Or override `parse_response`.

    # Set this value or override `get_new_paginator`.
    next_page_token_jsonpath = "$.nextPageUrl"  # noqa: S105

    @property
    def authenticator(self) -> FlipkartAuthenticator:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        return FlipkartAuthenticator.create_for_stream(
            self,
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        headers = {"Authorization": f"Bearer {self.authenticator.access_token}"}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Create a new pagination helper instance.

        If the source API can make use of the `next_page_token_jsonpath`
        attribute, or it contains a `X-Next-Page` header in the response
        then you can remove this method.

        If you need custom pagination that uses page numbers, "next" links, or
        other approaches, please read the guide: https://sdk.meltano.com/en/v0.25.0/guides/pagination-classes.html.

        Returns:
            A pagination helper instance.
        """
        return FlipkartPaginator(self.next_page_token_jsonpath) 

