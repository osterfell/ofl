"""Thin HTTP client for the Osterfell API. Standard library only."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE = "https://api.osterfell.com/v1"


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


class Client:
    def __init__(self, api_key: str | None = None, base: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key or os.environ.get("OFL_API_KEY", "")
        self.base = (base or os.environ.get("OFL_API_BASE") or DEFAULT_BASE).rstrip("/")
        self.timeout = timeout

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None, **query: Any) -> Any:
        url = self.base + path
        query = {k: v for k, v in query.items() if v is not None}
        if query:
            url += "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(
            url,
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ofl-python",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as e:
            try:
                message = json.loads(e.read()).get("error", e.reason)
            except ValueError:
                message = str(e.reason)
            raise ApiError(e.code, message) from None
        return json.loads(raw) if raw else None

    def search(self, filters: dict[str, Any] | None = None, sort: str = "price", limit: int = 20) -> list[dict[str, Any]]:
        return self._call("POST", "/offers/search", {"filters": filters or {}, "sort": sort, "limit": limit})["offers"]

    def create(self, offer_id: int, image: str, disk_gb: int = 40,
               bid: float | None = None, onstart: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"offer_id": offer_id, "image": image, "disk_gb": disk_gb,
                                "interruptible": bid is not None}
        if bid is not None:
            body["bid_eur_h"] = bid
        if onstart:
            body["onstart"] = onstart
        return self._call("POST", "/instances", body)

    def instances(self) -> list[dict[str, Any]]:
        return self._call("GET", "/instances")["instances"]

    def instance(self, instance_id: str) -> dict[str, Any]:
        return self._call("GET", f"/instances/{instance_id}")

    def stop(self, instance_id: str) -> dict[str, Any]:
        return self._call("POST", f"/instances/{instance_id}/stop")

    def destroy(self, instance_id: str) -> None:
        self._call("DELETE", f"/instances/{instance_id}")

    def logs(self, instance_id: str, tail: int = 200) -> str:
        return self._call("GET", f"/instances/{instance_id}/logs", tail=tail)["text"]

    def balance(self) -> dict[str, Any]:
        return self._call("GET", "/account/balance")
