from typing import List, Dict, Any, Optional
import httpx
from src.logger import logger


class JellyfinClient:
    """Client for interacting with Jellyfin API"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.client = httpx.Client(verify=False, timeout=30.0)

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "X-Emby-Authorization": (
                'MediaBrowser Client="ArrCleaner", Device="Python", '
                'DeviceId="arr-cleaner-001", Version="1.0.0"'
            )
        }

        if include_auth and self.access_token:
            headers["X-Emby-Token"] = self.access_token

        return headers

    def authenticate(self) -> bool:
        """Authenticate with Jellyfin and get access token"""
        logger.info(f"[cyan]Authenticating with Jellyfin as {self.username}[/cyan]")

        url = f"{self.base_url}/Users/AuthenticateByName"
        payload = {
            "Username": self.username,
            "Pw": self.password
        }

        try:
            response = self.client.post(
                url,
                json=payload,
                headers=self._get_headers(include_auth=False)
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["AccessToken"]
            self.user_id = data["User"]["Id"]

            logger.info("[green]Successfully authenticated with Jellyfin[/green]")
            return True

        except httpx.HTTPError as e:
            logger.error(f"[red]Failed to authenticate with Jellyfin: {e}[/red]")
            return False

    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users from Jellyfin"""
        logger.info("[cyan]Fetching all Jellyfin users[/cyan]")

        url = f"{self.base_url}/Users"

        try:
            response = self.client.get(url, headers=self._get_headers())
            response.raise_for_status()

            users = response.json()
            logger.info(f"[green]Found {len(users)} users[/green]")
            return users

        except httpx.HTTPError as e:
            logger.error(f"[red]Failed to get users: {e}[/red]")
            return []

    def get_watched_movies(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all watched movies for a specific user"""
        logger.info(f"[cyan]Fetching watched movies for user {user_id}[/cyan]")

        url = f"{self.base_url}/Users/{user_id}/Items"
        params = {
            "IncludeItemTypes": "Movie",
            "Recursive": "true",
            "IsPlayed": "true",
            "Fields": "Path,ProviderIds,MediaSources"
        }

        try:
            response = self.client.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()
            movies = data.get("Items", [])
            logger.info(f"[green]Found {len(movies)} watched movies[/green]")
            return movies

        except httpx.HTTPError as e:
            logger.error(f"[red]Failed to get watched movies: {e}[/red]")
            return []

    def get_watched_series(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all series with watch status for a specific user"""
        logger.info(f"[cyan]Fetching series for user {user_id}[/cyan]")

        url = f"{self.base_url}/Users/{user_id}/Items"
        params = {
            "IncludeItemTypes": "Series",
            "Recursive": "true",
            "Fields": "Path,ProviderIds,UserData"
        }

        try:
            response = self.client.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()
            series = data.get("Items", [])
            logger.info(f"[green]Found {len(series)} series[/green]")
            return series

        except httpx.HTTPError as e:
            logger.error(f"[red]Failed to get series: {e}[/red]")
            return []

    def get_series_details(self, series_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a series including episodes"""
        url = f"{self.base_url}/Users/{user_id}/Items/{series_id}"
        params = {
            "Fields": "Path,ProviderIds,UserData,RecursiveItemCount"
        }

        try:
            response = self.client.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"[red]Failed to get series details: {e}[/red]")
            return {}

    def get_series_episodes(self, series_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all episodes for a series"""
        url = f"{self.base_url}/Shows/{series_id}/Episodes"
        params = {
            "UserId": user_id,
            "Fields": "UserData"
        }

        try:
            response = self.client.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()
            return data.get("Items", [])

        except httpx.HTTPError as e:
            logger.error(f"[red]Failed to get series episodes: {e}[/red]")
            return []

    def is_series_fully_watched(self, series_id: str, user_id: str) -> tuple[bool, int, int]:
        """
        Check if a series is fully watched by a user
        Returns: (is_fully_watched, watched_count, total_count)
        """
        episodes = self.get_series_episodes(series_id, user_id)

        if not episodes:
            return False, 0, 0

        total_episodes = len(episodes)
        watched_episodes = sum(
            1 for ep in episodes
            if ep.get("UserData", {}).get("Played", False)
        )

        is_fully_watched = watched_episodes == total_episodes and total_episodes > 0

        return is_fully_watched, watched_episodes, total_episodes

    def close(self):
        """Close the HTTP client"""
        self.client.close()
