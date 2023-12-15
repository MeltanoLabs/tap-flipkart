"""Stream type classes for tap-flipkart."""

from __future__ import annotations

import typing as t
from pathlib import Path
import requests

from tap_flipkart.client import FlipkartStream
from singer_sdk import metrics
from singer_sdk.streams.rest import _TToken

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class ReturnsStream(FlipkartStream):
    """Define custom stream."""

    name = "returns"
    api_version = "v2"
    path = f"/{api_version}/returns"
    records_jsonpath = "$.returnItems[*]"
    primary_keys: t.ClassVar[list[str]] = ["returnId"]
    schema_filepath = SCHEMAS_DIR / "returns.json"
    rest_method = "GET"
    next_page_token_jsonpath = "$.nextUrl"

    def get_url_params(
        self,
        context: dict | None,  # noqa: ARG002
        next_page_token: _TToken | None,  # noqa: ARG002
    ) -> dict[str, t.Any] | str:
        if next_page_token:
            return {}
        return {
            "source": context["source"]
        }
    
    def prepare_request(
        self,
        context: dict | None,
        next_page_token: _TToken | None,
    ) -> requests.PreparedRequest:
        """Prepare a request object for this stream.

        If partitioning is supported, the `context` object will contain the partition
        definitions. Pagination information can be parsed from `next_page_token` if
        `next_page_token` is not None.

        Args:
            context: Stream partition or context dictionary.
            next_page_token: Token, page number or any request argument to request the
                next page of data.

        Returns:
            Build a request with the stream's URL, path, query parameters,
            HTTP headers and authenticator.
        """
        request = super().prepare_request(context, next_page_token)
        if next_page_token:
            request.url = self.url_base + f"/{self.api_version}" + next_page_token
        return request

    @property
    def partitions(self) -> list[dict] | None:
        """Get stream partitions.

        Developers may override this property to provide a default partitions list.

        By default, this method returns a list of any partitions which are already
        defined in state, otherwise None.

        Returns:
            A list of partition key dicts (if applicable), otherwise `None`.
        """
        return [{"source": "courier_return"}, {"source": "customer_return"}]

    def post_process(
        self,
        row: dict,
        context: dict | None = None,  # noqa: ARG002
    ) -> dict | None:
        """As needed, append or transform raw data to match expected structure.

        Optional. This method gives developers an opportunity to "clean up" the results
        prior to returning records to the downstream tap - for instance: cleaning,
        renaming, or appending properties to the raw record result returned from the
        API.

        Developers may also return `None` from this method to filter out
        invalid or not-applicable records from the stream.

        Args:
            row: Individual record in the stream.
            context: Stream partition or context dictionary.

        Returns:
            The resulting record dict, or `None` if the record should be excluded.
        """
        row["return_source"] = context["source"]
        return row

class ShipmentsStream(FlipkartStream):
    """Define custom stream."""

    name = "shipments"
    path = "/v3/shipments/filter"
    records_jsonpath = "$.shipments[*]"
    primary_keys: t.ClassVar[list[str]] = ["shipmentId"]
    schema_filepath = SCHEMAS_DIR / "shipments.json"
    rest_method = "POST"

    def prepare_request_payload(
        self,
        context: dict | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ARG002, ANN401
    ) -> dict | None:
        """Prepare the data payload for the REST API request.

        By default, no payload will be sent (return None).

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary with the JSON body for a POST requests.
        """
        return {
            "filter": context["filter"],
            "pagination": {
                "pageSize": 20
            },
            "sort": {
                "field": "orderDate",
                "order": "asc"
            }
        }

    @property
    def partitions(self) -> list[dict] | None:
        """Get stream partitions.

        Developers may override this property to provide a default partitions list.

        By default, this method returns a list of any partitions which are already
        defined in state, otherwise None.

        Returns:
            A list of partition key dicts (if applicable), otherwise `None`.
        """
        return [
            {
                "filter": {
                    "states": ["APPROVED"],
                    "type": "preDispatch"
                }
            },
            {
                "filter": {
                    "states": ["PACKING_IN_PROGRESS"],
                    "type": "preDispatch"
                }
            },
                        {
                "filter": {
                    "states": ["PACKED"],
                    "type": "preDispatch"
                }
            },
            {
                "filter": {
                    "states": ["FORM_FAILED"],
                    "type": "preDispatch"
                }
            },
            {
                "filter": {
                    "states": ["READY_TO_DISPATCH"],
                    "type": "preDispatch"
                }
            },
            {
                "filter": {
                    "states": ["SHIPPED"],
                    "type": "postDispatch"
                }
            },
            {
                "filter": {
                    "states": ["DELIVERED"],
                    "type": "postDispatch"
                }
            },
            {
                "filter": {
                    "states": ["PICKUP_COMPLETE"],
                    "type": "postDispatch"
                }
            },
            {
                "filter": {
                    "states": ["CANCELLED"],
                    "type": "cancelled",
                    "cancellationType": "sellerCancellation"
                }
            },
            # TODO: these requests fail
            # {
            #     "filter": {
            #         "states": ["CANCELLED"],
            #         "type": "cancelled",
            #         "cancellationType": "marketplaceCancellation"
            #     }
            # },
            # {
            #     "filter": {
            #         "states": ["CANCELLED"],
            #         "type": "cancelled",
            #         "cancellationType": "buyerCancellation"
            #     }
            # }
        ]

    def post_process(
        self,
        row: dict,
        context: dict | None = None,  # noqa: ARG002
    ) -> dict | None:
        """As needed, append or transform raw data to match expected structure.

        Optional. This method gives developers an opportunity to "clean up" the results
        prior to returning records to the downstream tap - for instance: cleaning,
        renaming, or appending properties to the raw record result returned from the
        API.

        Developers may also return `None` from this method to filter out
        invalid or not-applicable records from the stream.

        Args:
            row: Individual record in the stream.
            context: Stream partition or context dictionary.

        Returns:
            The resulting record dict, or `None` if the record should be excluded.
        """
        row["shipment_status_state"] = context["filter"]["states"][0]
        row["shipment_status_type"] = context["filter"]["type"]
        row["shipment_status_cancellation_type"] = context["filter"].get("cancellationType")
        return row

    def request_records(self, context: dict | None) -> t.Iterable[dict]:
        """Request records from REST endpoint(s), returning response records.

        If pagination is detected, pages will be recursed automatically.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            An item for every record in the response.
        """
        paginator = self.get_new_paginator()
        decorated_request = self.request_decorator(self._request)

        with metrics.http_request_counter(self.name, self.path) as request_counter:
            request_counter.context = context

            first = True
            while not paginator.finished:
                if first:
                    first = False
                    prepared_request = self.prepare_request(
                        context,
                        next_page_token=paginator.current_value,
                    )
                else:
                    # It wants you to switch from POST to GET once you get a pagination URL
                    url = "".join([self.url_base, paginator.current_value])
                    prepared_request = self.build_prepared_request(
                        method="GET",
                        url=url,
                    )
                resp = decorated_request(prepared_request, context)
                request_counter.increment()
                self.update_sync_costs(prepared_request, resp, context)
                yield from self.parse_response(resp)
                paginator.advance(resp)
