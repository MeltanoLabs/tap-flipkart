from singer_sdk.pagination import JSONPathPaginator

from requests import Response

class FlipkartPaginator(JSONPathPaginator):

    def has_more(self, response: Response) -> bool:  # noqa: ARG002
        """Override this method to check if the endpoint has any pages left.

        Args:
            response: API response object.

        Returns:
            Boolean flag used to indicate if the endpoint has more pages.
        """
        return response.json().get("hasMore")
