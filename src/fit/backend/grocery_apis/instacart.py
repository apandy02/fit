import dataclasses
from typing import Any, Iterable, Mapping

import httpx


class InstacartError(Exception):
    """Raised when Instacart API returns an error response or network fails."""


@dataclasses.dataclass(slots=True)
class InstacartClient:
    """Thin wrapper around Instacart Developer Platform API.

    - API overview: https://docs.instacart.com/developer_platform_api/api/overview
    - Create shopping list page: https://docs.instacart.com/developer_platform_api/api/products/create_shopping_list_page

    Usage:
        client = InstacartClient(api_key="...", base_url="https://connect.instacart.com")
        url = client.create_shopping_list_page(
            title="My list",
            line_items=[{"name": "tomato soup", "quantity": 1, "unit": "can"}],
        )

    Notes:
        - This uses httpx to match existing code patterns in trackers.
        - Raises InstacartError with response details on non-2xx.
    """

    api_key: str
    base_url: str = "https://connect.instacart.com"
    timeout_seconds: float = 15.0

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        url = f"{self.base_url.rstrip('/')}{path}"
        try:
            resp = httpx.post(
                url, json=payload, headers=self._headers(), timeout=self.timeout_seconds
            )
        except httpx.HTTPError as e:
            raise InstacartError(f"Network error calling Instacart: {e}") from e

        if resp.status_code >= 400:
            # Try to surface server-provided message when available
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            raise InstacartError(f"Instacart error {resp.status_code}: {data}")

        try:
            return resp.json()
        except ValueError as e:
            raise InstacartError("Invalid JSON in Instacart response") from e

    def create_shopping_list_page(
        self,
        *,
        title: str,
        line_items: Iterable[Mapping[str, Any]],
        image_url: str | None = None,
        link_type: str | None = None,  # 'shopping_list' (default) or 'recipe'
        expires_in_days: int | None = None,
        instructions: Iterable[str] | None = None,
        partner_linkback_url: str | None = None,
        enable_pantry_items: bool | None = None,
        accept_language: str | None = None,  # e.g., 'en-US', 'en-CA', 'fr-CA'
    ) -> str:
        """Create a shopping list page and return the products_link_url.

        Required fields per docs: title, line_items (with at least name)
        Optional fields are passed when provided. Units must match Instacart's
        supported list; the API performs matching.
        """

        # Best practice TODO:
        # Cache the generated shopping list page URL and reuse it.
        # Don't generate a new URL unless the shopping list changes.

        if not title or not list(line_items):
            raise ValueError("Both title and at least one line item are required")

        body: dict[str, Any] = {
            "title": title,
            "line_items": list(line_items),
        }

        if image_url:
            body["image_url"] = image_url
        if link_type:
            body["link_type"] = link_type
        if expires_in_days is not None:
            body["expires_in"] = int(expires_in_days)
        if instructions:
            body["instructions"] = list(instructions)
        if partner_linkback_url is not None or enable_pantry_items is not None:
            body["landing_page_configuration"] = {}
            if partner_linkback_url is not None:
                body["landing_page_configuration"][
                    "partner_linkback_url"
                ] = partner_linkback_url
            if enable_pantry_items is not None:
                body["landing_page_configuration"]["enable_pantry_items"] = bool(
                    enable_pantry_items
                )

        # Allow caller to override Accept-Language for Canadian locales, etc.
        headers = self._headers()
        if accept_language:
            headers["Accept-Language"] = accept_language

        url_path = "/idp/v1/products/products_link"
        try:
            url = f"{self.base_url.rstrip('/')}{url_path}"
            resp = httpx.post(
                url, json=body, headers=headers, timeout=self.timeout_seconds
            )
        except httpx.HTTPError as e:
            raise InstacartError(f"Network error calling Instacart: {e}") from e

        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = {"raw": resp.text}
            raise InstacartError(f"Instacart error {resp.status_code}: {detail}")

        try:
            data = resp.json()
        except ValueError as e:
            raise InstacartError("Invalid JSON in Instacart response") from e

        link = data.get("products_link_url")
        if not isinstance(link, str) or not link:
            raise InstacartError("Response missing 'products_link_url'")
        return link
