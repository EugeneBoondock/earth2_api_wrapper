from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import httpx
from .rate_limiter import get_rate_limiter


class Earth2Client:
    def __init__(
        self,
        cookie_jar: Optional[str] = None,
        csrf_token: Optional[str] = None,
        client: Optional[httpx.Client] = None,
        respect_rate_limits: bool = True
    ):
        self.cookie_jar = cookie_jar
        self.csrf_token = csrf_token
        self._client = client or httpx.Client(timeout=30)
        self._rate_limiter = get_rate_limiter() if respect_rate_limits else None

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "earth2-api-wrapper-py/0.2.1",
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
        # Rate limit authentication attempts to prevent abuse
        if self._rate_limiter:
            can_proceed, reason, _ = self._rate_limiter.can_make_request('https://app.earth2.io/login', 'POST')
            if not can_proceed:
                return {
                    "success": False,
                    "message": f"Authentication rate limited: {reason}"
                }

        try:
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            all_cookies = []

            # Step 1: Start OAuth flow by visiting the main login page
            login_page_response = self._client.get(
                "https://app.earth2.io/login",
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                },
                follow_redirects=False
            )

            # Step 2: Collect cookies
            if 'set-cookie' in login_page_response.headers:
                all_cookies.extend(login_page_response.headers['set-cookie'].split('; '))

            # Follow redirects from the main page until we reach Kinde
            current_response = login_page_response
            for _ in range(10):  # Safety limit
                if current_response.status_code in (301, 302, 303, 307, 308):
                    location = current_response.headers.get('location')
                    if location:
                        # This normalizes funky Earth2 URLs like 'https:auth.earth2.io'
                        location = self._normalize_auth_url(location)

                        current_response = self._client.get(
                            location,
                            headers={
                                "User-Agent": user_agent,
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                            },
                            follow_redirects=False
                        )

                        if 'set-cookie' in current_response.headers:
                            all_cookies.extend(current_response.headers['set-cookie'].split('; '))

                        # If we reach the auth email form, break
                        if 'auth.earth2.io' in location and '/email' in location:
                            break
                else:
                    # If not redirected to Kinde, this was the final response
                    break

            # Step 5: Extract and submit email form
            email_page_html = current_response.text

            # Extract form action and hidden inputs
            action_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', email_page_html)
            if action_match:
                email_form_action = self._normalize_auth_url(action_match.group(1))

                # Extract hidden inputs
                email_data = {}
                hidden_inputs = re.findall(
                    r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
                    email_page_html
                )
                for name, value in hidden_inputs:
                    email_data[name] = value

                # Add form data
                email_data['email'] = email

                email_response = self._client.post(
                    email_form_action,
                    data=email_data,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    follow_redirects=False
                )

                if 'set-cookie' in email_response.headers:
                    all_cookies.extend(email_response.headers['set-cookie'].split('; '))

                # Follow redirects after email submission
                current_response = email_response
                for _ in range(10):  # Safety limit
                    if current_response.status_code in (301, 302, 303, 307, 308):
                        location = current_response.headers.get('location')
                        if location:

                            # Normalize this Earth2 URL quirk
                            location = self._normalize_auth_url(location)

                            current_response = self._client.get(
                                location,
                                headers={
                                    "User-Agent": user_agent,
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                                },
                                follow_redirects=False
                            )

                            if 'set-cookie' in current_response.headers:
                                all_cookies.extend(current_response.headers['set-cookie'].split('; '))

                            # If we reach password/login/register page, we're good
                            if any(keyword in location for keyword in ['/password', '/login', '/register']):
                                break

                            if current_response.status_code in (301, 302, 303, 307, 308):
                                continue
                            else:
                                break
                        else:
                            break
                    else:
                        break

            # Step 6: Get password page if needed
            if current_response.status_code in (301, 302, 303, 307, 308):
                location = current_response.headers.get('location')
                if location:
                    # Normalize auth URL
                    location = self._normalize_auth_url(location)

                    current_response = self._client.get(
                        location,
                        headers={
                            "User-Agent": user_agent,
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                        },
                        follow_redirects=False
                    )

                    if 'set-cookie' in current_response.headers:
                        all_cookies.extend(current_response.headers['set-cookie'].split('; '))

            # Step 7: Extract and submit password form
            password_page_html = current_response.text

            # Extract form action and hidden inputs
            action_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', password_page_html)
            if action_match:

                password_form_action = self._normalize_auth_url(action_match.group(1))

                # Extract hidden inputs
                password_data = {}
                hidden_inputs = re.findall(
                    r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
                    password_page_html
                )
                for name, value in hidden_inputs:
                    password_data[name] = value

                # Add password
                password_data["password"] = password

                password_response = self._client.post(
                    password_form_action,
                    data=password_data,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    follow_redirects=False
                )

                if 'set-cookie' in password_response.headers:
                    all_cookies.extend(password_response.headers['set-cookie'].split('; '))

                # Follow remaining redirects back to Earth2 app
                current_response = password_response
                for _ in range(20):  # Safety limit
                    if current_response.status_code in (301, 302, 303, 307, 308):
                        location = current_response.headers.get('location')
                        if location:
                            # Final chain of redirects back to app.earth2.io
                            if 'app.earth2.io' in location:
                                break

                            if current_response.status_code in (301, 302, 303, 307, 308):
                                location = current_response.headers.get('location')
                                if location:

                                    location = self._normalize_auth_url(location)

                                    current_response = self._client.get(
                                        location,
                                        headers={
                                            "User-Agent": user_agent,
                                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                                        },
                                        follow_redirects=False
                                    )

                                    if 'set-cookie' in current_response.headers:
                                        all_cookies.extend(current_response.headers['set-cookie'].split('; '))

                                    # Check if we're back at Earth2 domain
                                    if 'app.earth2.io' in location:
                                        break

                                else:
                                    break

                            else:
                                break

                        else:
                            break
                    else:
                        break

            # Store cookies
            self.cookie_jar = "; ".join(all_cookies)

            if self._rate_limiter:
                self._rate_limiter.record_request('https://app.earth2.io/login', 'POST')

            return {
                "success": True,
                "message": "Authentication successful! OAuth flow completed and cookies have been set."
            }

        except Exception as error:
            if self._rate_limiter:
                self._rate_limiter.record_error('https://app.earth2.io/login')

            return {
                "success": False,
                "message": f"Authentication error: {str(error)}"
            }

    def check_session_validity(self) -> Dict[str, Any]:
        """Check if the current session cookies are still valid"""
        try:

            response = self._client.get(
                "https://app.earth2.io/api/v1/avatar_sales",
                headers=self._headers(),
                follow_redirects=False
            )

            if response.status_code == 200:
                return {"isValid": True, "needsReauth": False}

            else:

                return {
                    "isValid": False,
                    "needsReauth": True,
                    "status": response.status_code
                }

        except Exception:

            return {
                "isValid": False,
                "needsReauth": True,
                "error": "Network error"
            }

    def _get_json(self, url: str) -> Dict[str, Any]:
        """Helper method to get JSON from an API endpoint with rate limiting"""
        if self._rate_limiter:
            can_proceed, reason, cached_response = self._rate_limiter.can_make_request(url, 'GET')

            if cached_response is not None:
                return cached_response

            if not can_proceed:
                raise Exception(f"Rate limit exceeded: {reason}")

        try:
            response = self._client.get(url, headers=self._headers(), follow_redirects=True)
            response.raise_for_status()
            result = response.json()

            if self._rate_limiter:
                self._rate_limiter.record_request(url, 'GET')
                self._rate_limiter.cache_response(url, 'GET', result)

            return result

        except Exception as e:
            if self._rate_limiter:
                status_code = None
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    status_code = e.response.status_code
                self._rate_limiter.record_error(url, status_code)
            raise

    def get_landing_metrics(self) -> Dict[str, Any]:
        """Get landing page metrics"""
        return self._get_json("https://r.earth2.io/landing/metrics")

    def get_trending_places(self, days: int = 30) -> Dict[str, Any]:
        """Get trending places"""
        return self._get_json("https://r.earth2.io/landing/trending_places")

    def get_territory_release_winners(self) -> Dict[str, Any]:
        """Get territory release winners"""
        return self._get_json("https://r.earth2.io/landing/territory_release_winners")

    def get_property(self, property_id: str) -> Dict[str, Any]:
        """Get property details by ID"""
        return self._get_json(f"https://r.earth2.io/landfields/{property_id}")

    def search_market(
        self,
        country: Optional[str] = None,
        landfieldTier: Optional[str] = None,
        tileClass: Optional[str] = None,
        tileCount: Optional[str] = None,
        page: int = 1,
        items: int = 100,
        search: str = "",
        searchTerms: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Search marketplace"""
        params = {
            "page": page,
            "items": items,
            "search": search,
        }

        if country:
            params["country"] = country
        if landfieldTier:
            params["landfieldTier"] = landfieldTier
        if tileClass:
            params["tileClass"] = tileClass
        if tileCount:
            params["tileCount"] = tileCount
        if searchTerms:
            params["searchTerms"] = searchTerms

        params.update(kwargs)

        url = "https://r.earth2.io/marketplace"
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        full_url = f"{url}?{query_string}"

        return self._get_json(full_url)

    def get_market_floor(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Get market floor price per tile"""
        url = "https://r.earth2.io/marketplace"
        query_params = {
            "items": "24",
            "page": "1",
            "search": "",
            "sorting": "price_per_tile"
        }

        if params.get("country"):
            query_params["country"] = params["country"]
        if params.get("tileCount"):
            query_params["tileCount"] = params["tileCount"]
        if params.get("landfieldTier"):
            query_params["landfieldTier"] = params["landfieldTier"]
        if params.get("tileClass") and params.get("landfieldTier") == "1":
            query_params["tileClass"] = params["tileClass"]
        query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
        return self._get_json(f"{url}?{query_string}")

    def get_leaderboard_players(self, **params) -> Dict[str, Any]:
        """Get players leaderboard"""
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        url = "https://r.earth2.io/leaderboards/players"
        return self._get_json(f"{url}?{query_string}" if query_string else url)

    def get_leaderboard_countries(self, **params) -> Dict[str, Any]:
        """Get countries leaderboard"""
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        url = "https://r.earth2.io/leaderboards/landfield_countries"
        return self._get_json(f"{url}?{query_string}" if query_string else url)

    def get_leaderboard_player_countries(self, **params) -> Dict[str, Any]:
        """Get player countries leaderboard"""
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        url = "https://r.earth2.io/leaderboards/player_countries"
        return self._get_json(f"{url}?{query_string}" if query_string else url)

    def get_avatar_sales(self) -> Dict[str, Any]:
        """Get avatar sales data"""
        return self._get_json("https://r.earth2.io/avatar_sales")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information by ID"""
        return self._get_json(f"https://app.earth2.io/api/v2/user_info/{user_id}")

    def get_users(self, user_ids: List[str]) -> Dict[str, Any]:
        """Get multiple users by IDs (aggregate single-user endpoint)"""
        aggregated: List[Dict[str, Any]] = []
        for uid in user_ids:
            try:
                aggregated.append(self.get_user_info(uid))
            except Exception:
                # Skip invalid/unknown ids
                pass
        return {"data": aggregated}

    def get_resources(self, property_id: str) -> Dict[str, Any]:
        """Get property resources by ID"""
        return self._get_json(f"https://resources.earth2.io/v1/landfields/{property_id}/resources")

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics and usage information"""
        if not self._rate_limiter:
            return {"rate_limiting": "disabled"}
        return self._rate_limiter.get_stats()

    def clear_cache(self):
        """Clear the response cache"""
        if self._rate_limiter:
            self._rate_limiter.clear_cache()

    def set_cache_ttl(self, seconds: int):
        """Set cache time-to-live in seconds"""
        if self._rate_limiter:
            self._rate_limiter._cache_ttl = seconds
