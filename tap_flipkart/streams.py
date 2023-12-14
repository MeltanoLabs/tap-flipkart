"""Stream type classes for tap-flipkart."""

from __future__ import annotations

import typing as t
from pathlib import Path

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_flipkart.client import FlipkartStream
from singer_sdk import metrics

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

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
