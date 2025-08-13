from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import httpx


class Earth2Client:
    def __init__(self, cookie_jar: Optional[str] = None, csrf_token: Optional[str] = None, client: Optional[httpx.Client] = None):
        self.cookie_jar = cookie_jar
        self.csrf_token = csrf_token
        self._client = client or httpx.Client(timeout=30)

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "earth2-api-wrapper-py/0.1",
        }
        if self.cookie_jar:
            headers["Cookie"] = self.cookie_jar
        if self.csrf_token:
            headers["X-CSRF-TOKEN"] = self.csrf_token
            headers["X-XSRF-TOKEN"] = self.csrf_token
            headers["X-CsrfToken"] = self.csrf_token
        return headers

    def get_landing_metrics(self) -> Any:
        return self._get_json("https://r.earth2.io/landing/metrics")

    def get_trending_places(self) -> Dict[str, Any]:
        j = self._get_json("https://r.earth2.io/landing/trending_places")
        data = j.get("data", []) if isinstance(j, dict) else []
        normalized = []
        for item in data:
            a = (item or {}).get("attributes", {})
            normalized.append(
                {
                    "id": item.get("id"),
                    "tier": a.get("landfieldTier"),
                    "placeCode": a.get("placeCode"),
                    "placeName": a.get("placeName"),
                    "tilesSold": a.get("tilesSold"),
                    "tilePrice": a.get("tilePrice"),
                    "timeframeDays": a.get("timeframeDays"),
                    "country": a.get("country"),
                    "center": a.get("center"),
                }
            )
        return {"data": normalized}

    def get_territory_release_winners(self) -> Dict[str, Any]:
        j = self._get_json("https://r.earth2.io/landing/territory_release_winners")
        data = j.get("data", []) if isinstance(j, dict) else []
        normalized = []
        for item in data:
            a = (item or {}).get("attributes", {})
            normalized.append(
                {
                    "id": item.get("id"),
                    "territoryCode": a.get("territoryCode"),
                    "territoryName": a.get("territoryName"),
                    "country": a.get("country"),
                    "countryName": a.get("countryName"),
                    "votesValue": a.get("votesValue"),
                    "votesT1": a.get("votesT1"),
                    "votesT2": a.get("votesT2"),
                    "votesEsnc": a.get("votesEsnc"),
                    "releaseAt": a.get("releaseAt"),
                    "center": a.get("center"),
                }
            )
        return {"data": normalized}

    def get_avatar_sales(self) -> Dict[str, Any]:
        return self._get_json("https://r.earth2.io/avatar_sales")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        return self._get_json(f"https://app.earth2.io/api/v2/user_info/{user_id}")

    def get_users(self, user_ids: List[str]) -> Dict[str, Any]:
        params = [("ids", user_id) for user_id in user_ids]
        return self._get_json("https://app.earth2.io/users", params=params)

    def get_my_favorites(self) -> Dict[str, Any]:
        return self._get_json("https://r.earth2.io/api/v2/my/favorites")

    def get_property(self, id: str) -> Any:
        if not id:
            raise ValueError("id required")
        return self._get_json(f"https://r.earth2.io/landfields/{id}")

    def search_market(self, *, country: Optional[str] = None, landfieldTier: Optional[str] = None, tileClass: Optional[str] = None, tileCount: Optional[str] = None, page: int = 1, items: int = 100, search: str = "", searchTerms: Optional[List[str]] = None) -> Dict[str, Any]:
        url = httpx.URL("https://r.earth2.io/marketplace")
        params = {
            "sorting": "price_per_tile",
            "page": str(page),
            "items": str(items),
            "search": search,
        }
        if country:
            params["country"] = country
        if landfieldTier is not None:
            params["landfieldTier"] = str(landfieldTier)
        if tileClass is not None and landfieldTier == "1":
            params["tileClass"] = str(tileClass)
        if tileCount is not None:
            params["tileCount"] = str(tileCount)
        request = self._client.build_request("GET", url, params=params, headers=self._headers())
        resp = self._client.send(request)
        self._ensure_ok(resp, url)
        j = resp.json()
        landfields = j.get("landfields", []) if isinstance(j, dict) else []
        items_out = []
        for lf in landfields:
            ppt = (lf.get("price") or 0) / lf.get("tileCount") if (lf.get("price") and lf.get("tileCount")) else None
            if ppt is not None:
                items_out.append(
                    {
                        "id": lf.get("id"),
                        "description": lf.get("description"),
                        "location": lf.get("location"),
                        "country": lf.get("country"),
                        "tier": lf.get("landfieldTier"),
                        "tileClass": lf.get("tileClass"),
                        "tileCount": lf.get("tileCount"),
                        "price": lf.get("price"),
                        "ppt": ppt,
                        "thumbnail": lf.get("thumbnail"),
                    }
                )
        items_out.sort(key=lambda x: x["ppt"])  # type: ignore[index]
        return {"raw": j, "items": items_out, "count": int(j.get("count", 0)) if isinstance(j, dict) else 0}

    def get_leaderboard(self, kind: str = "players", **params: Any) -> Any:
        if kind not in ("players", "countries", "player_countries"):
            raise ValueError("invalid leaderboard kind")
        path = {
            "players": "players",
            "countries": "landfield_countries",
            "player_countries": "player_countries",
        }[kind]
        url = httpx.URL(f"https://r.earth2.io/leaderboards/{path}")
        req = self._client.build_request("GET", url, params={k: v for k, v in params.items() if v is not None}, headers=self._headers())
        resp = self._client.send(req)
        self._ensure_ok(resp, url)
        return resp.json()

    def get_resources(self, property_id: str) -> Any:
        if not property_id:
            raise ValueError("property_id required")
        url = f"https://resources.earth2.io/v1/landfields/{property_id}/resources"
        req = self._client.build_request("GET", url, headers=self._headers())
        resp = self._client.send(req)
        self._ensure_ok(resp, url)
        return resp.json()

    def _get_json(self, url: str) -> Any:
        resp = self._client.get(url, headers=self._headers())
        self._ensure_ok(resp, url)
        return resp.json()

    @staticmethod
    def _ensure_ok(resp: httpx.Response, url: Any) -> None:
        if resp.status_code < 200 or resp.status_code >= 300:
            text = None
            try:
                text = resp.text
            except Exception:
                pass
            raise RuntimeError(f"GET {url} failed: {resp.status_code} {text[:200] if text else ''}")


