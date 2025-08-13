from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import httpx


class Earth2Client:
    def __init__(
        self,
        cookie_jar: Optional[str] = None,
        csrf_token: Optional[str] = None,
        client: Optional[httpx.Client] = None
    ):
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

            return {
                "success": True,
                "message": "Authentication successful! OAuth flow completed and cookies have been set."
            }

        except Exception as error:

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
        """Helper method to get JSON from an API endpoint"""
        response = self._client.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def get_landing_metrics(self) -> Dict[str, Any]:
        """Get landing page metrics"""
        return self._get_json("https://app.earth2.io/api/v1/metrics/landing_page")

    def get_trending_places(self, days: int = 30) -> Dict[str, Any]:
        """Get trending places"""
        return self._get_json(f"https://app.earth2.io/api/v1/trending_places?days={days}")

    def get_territory_release_winners(self) -> Dict[str, Any]:
        """Get territory release winners"""
        return self._get_json("https://app.earth2.io/api/v1/territory_release_winners")

    def get_property(self, property_id: str) -> Dict[str, Any]:
        """Get property details by ID"""
        return self._get_json(f"https://app.earth2.io/api/v1/property/{property_id}")

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

        url = "https://app.earth2.io/api/v1/marketplace"
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        full_url = f"{url}?{query_string}"

        return self._get_json(full_url)

    def get_leaderboard(
        self,
        type: str = "players",  # noqa: A002
        sort_by: str = "tiles_count",
        country: Optional[str] = None,
        continent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get leaderboard"""
        params = {"type": type, "sort_by": sort_by}
        if country:
            params["country"] = country
        if continent:
            params["continent"] = continent

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return self._get_json(f"https://app.earth2.io/api/v1/leaderboard?{query_string}")

    def get_avatar_sales(self) -> Dict[str, Any]:
        """Get avatar sales data"""
        return self._get_json("https://app.earth2.io/api/v1/avatar_sales")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information by ID"""
        return self._get_json(f"https://app.earth2.io/api/v1/user/{user_id}")

    def get_users(self, user_ids: List[str]) -> Dict[str, Any]:
        """Get multiple users by IDs"""
        user_ids_str = ",".join(user_ids)
        return self._get_json(f"https://app.earth2.io/api/v1/users?ids={user_ids_str}")

    def get_my_favorites(self) -> Dict[str, Any]:
        """Get user's favorite properties (requires authentication)"""
        return self._get_json("https://app.earth2.io/api/v1/user/favorites")

    def get_resources(self, property_id: str) -> Dict[str, Any]:
        """Get property resources by ID"""
        return self._get_json(f"https://app.earth2.io/api/v1/property/{property_id}/resources")
