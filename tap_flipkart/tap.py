"""Flipkart tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
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
        # th.Property(
        #     "start_date",
        #     th.DateTimeType,
        #     description="The earliest record date to sync",
        # ),
    ).to_dict()

    def discover_streams(self) -> list[streams.FlipkartStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.ShipmentsStream(self),
        ]


if __name__ == "__main__":
    TapFlipkart.cli()
