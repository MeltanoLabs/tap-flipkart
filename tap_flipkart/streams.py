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
            # TODO: support customer_return and courier_return
            "source": "courier_return"
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

class ShipmentsStream(FlipkartStream):
    """Define custom stream."""

    name = "shipments"
    path = "/v3/shipments/filter"
    records_jsonpath = "$.shipments[*]"
    primary_keys: t.ClassVar[list[str]] = ["shipmentId"]
    schema_filepath = SCHEMAS_DIR / "shipments.json"
    rest_method = "POST"

    # This operation should be used if hasMore is true in the response of POST /v3/shipments/filter API, so that the client can fetch the next set of shipment which qualify the earlier defined filter criteria. User need not build this URL by themselves, just use the URL returned as nextPageUrl in the response of POST /v3/shipments/filter or GET /v3/shipments/filter.


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
        # TODO: how to configure all these variations?
        return {
            "filter": {
                "states": ["APPROVED" , "PACKING_IN_PROGRESS", "PACKED", "FORM_FAILED", "READY_TO_DISPATCH"],
                "type": "preDispatch"
            },
            "pagination": {
                "pageSize": 20
            },
            "sort": {
                "field": "orderDate",
                "order": "asc"
            }
        }
        # 
        # Delivered eventually failed probably due to too many requests. Together is less than all individually. Maybe check if theres overlap?
        # return {
        #     "filter": {
        #         "states": ["PICKUP_COMPLETE"],
        #         # "SHIPPED", "DELIVERED", "PICKUP_COMPLETE"],
        #         "type": "postDispatch"
        #     },
        #     "pagination": {
        #         "pageSize": 20
        #     },
        #     "sort": {
        #         "field": "orderDate",
        #         "order": "asc"
        #     }
        # }
        # return {
        #     "filter": {
        #         "states": ["CANCELLED"],
        #         "type": "cancelled",
        #         # marketplaceCancellation and buyerCancellation are listed as types but dont work
        #         "cancellationType": "sellerCancellation"
        #         # marketplaceCancellation, sellerCancellation, buyerCancellation
        #     },
        #     "pagination": {
        #         "pageSize": 20
        #     },
        #     "sort": {
        #         "field": "orderDate",
        #         "order": "asc"
        #     }
        # }

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
