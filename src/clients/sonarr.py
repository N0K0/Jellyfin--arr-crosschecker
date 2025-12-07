from typing import List, Dict, Any
from    pyarr import SonarrAPI
from src.logger import logger


class SonarrClient:
    """Client for interacting with Sonarr API"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # PyArr expects URL without /api
        self.client = SonarrAPI(self.base_url, self.api_key)

    def test_connection(self) -> bool:
        """Test connection to Sonarr"""
        logger.info("[cyan]Testing connection to Sonarr[/cyan]")

        try:
            self.client.get_system_status()
            logger.info("[green]Successfully connected to Sonarr[/green]")
            return True
        except Exception as e:
            logger.error(f"[red]Failed to connect to Sonarr: {e}[/red]")
            return False

    def get_all_series(self) -> List[Dict[str, Any]]:
        """Get all series from Sonarr"""
        logger.info("[cyan]Fetching all series from Sonarr[/cyan]")

        try:
            series = self.client.get_series()
            logger.info(f"[green]Found {len(series)} series in Sonarr[/green]")
            return series
        except Exception as e:
            logger.error(f"[red]Failed to get series from Sonarr: {e}[/red]")
            return []

    def get_series_by_tvdb_id(self, tvdb_id: str) -> Dict[str, Any]:
        """Get a specific series by TVDB ID"""
        try:
            series_list = self.client.get_series()
            for series in series_list:
                if str(series.get("tvdbId")) == str(tvdb_id):
                    return series
            return {}
        except Exception as e:
            logger.error(f"[red]Failed to get series by TVDB ID: {e}[/red]")
            return {}
