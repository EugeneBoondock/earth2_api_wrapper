from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

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

    def _normalize_auth_url(self, raw: str) -> str:
        """Helper to normalize Earth2's quirky OAuth URLs"""
        url = raw
        if url.startswith('/'):
            url = f"https://auth.earth2.io{url}"
        elif not url.startswith('http'):
            url = f"https://auth.earth2.io/{url}"
        # Replace illegal psid: with psid=
        url = url.replace('psid:', 'psid=')
        return url

    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate with email/password using Earth2's Kinde OAuth flow"""
        try:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            all_cookies = []

            # Step 1: Start OAuth flow by visiting the main login page
            login_page_response = self._client.get(
                "https://app.earth2.io/login",
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
                follow_redirects=False
            )

            if login_page_response.cookies:
                all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in login_page_response.cookies])

            # Step 2: Handle the first redirect (301 to /login/)
            location_header = login_page_response.headers.get('location')
            if not location_header:
                return {"success": False, "message": "No redirect found from login page"}

            if location_header.startswith('/'):
                location_header = f"https://app.earth2.io{location_header}"

            step2_response = self._client.get(
                location_header,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Cookie": "; ".join(all_cookies),
                },
                follow_redirects=False
            )

            if step2_response.cookies:
                all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in step2_response.cookies])

            # Step 3: Follow the OAuth redirect (302 to auth.earth2.io)
            oauth_url = step2_response.headers.get('location')
            if not oauth_url:
                return {"success": False, "message": "No OAuth redirect found from /login/ page"}

            oauth_response = self._client.get(
                oauth_url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Cookie": "; ".join(all_cookies),
                },
                follow_redirects=False
            )

            if oauth_response.cookies:
                all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in oauth_response.cookies])

            # Step 4: Follow redirects to get to the email form
            current_response = oauth_response
            redirect_count = 0
            while current_response.status_code >= 300 and current_response.status_code < 400 and redirect_count < 5:
                next_url_raw = current_response.headers.get('location')
                if not next_url_raw:
                    break
                next_url = self._normalize_auth_url(next_url_raw)
                
                current_response = self._client.get(
                    next_url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Cookie": "; ".join(all_cookies),
                    },
                    follow_redirects=False
                )

                if current_response.cookies:
                    all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in current_response.cookies])
                redirect_count += 1

            # Step 5: Extract and submit email form
            email_page_html = current_response.text
            email_form_action = str(current_response.url)
            
            form_match = re.search(r'<form[^>]*action=[\'\"](.*?)[\'\"][^>]*>', email_page_html)
            if form_match:
                email_form_action = self._normalize_auth_url(form_match.group(1))

            # Extract hidden fields
            hidden_inputs = re.findall(r'<input[^>]*type=[\'\"](hidden|csrf)[\'\"][^>]*>', email_page_html)
            form_data = {"email": email}
            
            for input_tag in hidden_inputs:
                name_match = re.search(r'name=[\'\"](.*?)[\'\"]', input_tag)
                value_match = re.search(r'value=[\'\"](.*?)[\'\"]', input_tag)
                if name_match and value_match:
                    form_data[name_match.group(1)] = value_match.group(1)

            email_response = self._client.post(
                email_form_action,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://auth.earth2.io",
                    "Referer": str(current_response.url),
                    "Cookie": "; ".join(all_cookies),
                },
                data=form_data,
                follow_redirects=False
            )

            if email_response.cookies:
                all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in email_response.cookies])

            # Step 6: Follow redirects to password page
            password_page_response = email_response
            redirect_count = 0
            while password_page_response.status_code >= 300 and password_page_response.status_code < 400 and redirect_count < 5:
                next_url_raw = password_page_response.headers.get('location')
                if not next_url_raw:
                    break
                next_url = self._normalize_auth_url(next_url_raw)
                
                password_page_response = self._client.get(
                    next_url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Cookie": "; ".join(all_cookies),
                    },
                    follow_redirects=False
                )

                if password_page_response.cookies:
                    all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in password_page_response.cookies])
                redirect_count += 1

            # Step 7: Extract and submit password form
            password_page_html = password_page_response.text
            password_form_action = str(password_page_response.url)
            
            password_form_match = re.search(r'<form[^>]*action=[\'\"](.*?)[\'\"][^>]*>', password_page_html)
            if password_form_match:
                password_form_action = self._normalize_auth_url(password_form_match.group(1))

            password_hidden_inputs = re.findall(r'<input[^>]*type=[\'\"](hidden|csrf)[\'\"][^>]*>', password_page_html)
            password_form_data = {"password": password}
            
            for input_tag in password_hidden_inputs:
                name_match = re.search(r'name=[\'\"](.*?)[\'\"]', input_tag)
                value_match = re.search(r'value=[\'\"](.*?)[\'\"]', input_tag)
                if name_match and value_match:
                    password_form_data[name_match.group(1)] = value_match.group(1)

            password_response = self._client.post(
                password_form_action,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://auth.earth2.io",
                    "Referer": str(password_page_response.url),
                    "Cookie": "; ".join(all_cookies),
                },
                data=password_form_data,
                follow_redirects=False
            )

            if password_response.cookies:
                all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in password_response.cookies])

            # Step 8: Follow OAuth callback chain back to app.earth2.io
            current_url = password_response.headers.get('location')
            redirect_count = 0
            while current_url and redirect_count < 10:
                if current_url.startswith('/'):
                    current_url = f"https://app.earth2.io{current_url}"
                
                redirect_response = self._client.get(
                    current_url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Cookie": "; ".join(all_cookies),
                    },
                    follow_redirects=False
                )

                if redirect_response.cookies:
                    all_cookies.extend([f"{cookie.name}={cookie.value}" for cookie in redirect_response.cookies])

                current_url = redirect_response.headers.get('location')
                redirect_count += 1

                if current_url and 'app.earth2.io' in current_url:
                    break

            if redirect_count >= 10:
                return {"success": False, "message": "Too many redirects during OAuth flow"}

            # Store final cookies
            self.cookie_jar = "; ".join(all_cookies)
            
            return {
                "success": True,
                "message": "Authentication successful! OAuth flow completed and cookies have been set."
            }
                
        except Exception as error:
            return {
                "success": False,
                "message": f"Authentication error: {str(error)}"
            }

    def check_session_validity(self) -> Dict[str, bool]:
        """Check if current session is still valid"""
        if not self.cookie_jar:
            return {"isValid": False, "needsReauth": True}

        try:
            # Test session by calling a simple endpoint
            test_response = self._client.get(
                "https://r.earth2.io/avatar_sales?page=1&perPage=12",
                headers={
                    "User-Agent": "earth2-api-wrapper-py/0.1",
                    "Accept": "application/json, text/plain, */*",
                    "Cookie": self.cookie_jar,
                    "Referer": "https://app.earth2.io/",
                    "Origin": "https://app.earth2.io"
                }
            )

            if test_response.status_code in [401, 403]:
                return {"isValid": False, "needsReauth": True}

            return {"isValid": True, "needsReauth": False}

        except Exception:
            return {"isValid": False, "needsReauth": True}

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


