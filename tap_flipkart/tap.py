"""Flipkart tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_flipkart import streams


class TapFlipkart(Tap):
    """Flipkart tap class."""

    name = "tap-flipkart"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "client_id",
            th.StringType,
            required=True,
            secret=True,
            description="",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=True,
            secret=True,
            description="",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
        ),
        th.Property(
            "shipment_state_selections",
            th.ObjectType(
                th.Property(
                    "include",
                    th.ArrayType(th.StringType),
                    description="Shipment states to include.",
                ),
                th.Property(
                    "exclude",
                    th.ArrayType(th.StringType),
                    description="Shipment states to exclude.",
                ),
            ),
            description="An object of include or exclude options for shipment states. If left null then all available states will be selected.",
            default=None,
        )
    ).to_dict()

    def discover_streams(self) -> list[streams.FlipkartStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.ReturnsStream(self),
            streams.ShipmentsStream(self),
        ]


if __name__ == "__main__":
    TapFlipkart.cli()
