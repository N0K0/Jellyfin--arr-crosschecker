from typing import List, Dict, Any
from pyarr import RadarrAPI
from src.logger import logger


class RadarrClient:
    """Client for interacting with Radarr API"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # PyArr expects URL without /api
        self.client = RadarrAPI(self.base_url, self.api_key)

    def test_connection(self) -> bool:
        """Test connection to Radarr"""
        logger.info("[cyan]Testing connection to Radarr[/cyan]")

        try:
            self.client.get_system_status()
            logger.info("[green]Successfully connected to Radarr[/green]")
            return True
        except Exception as e:
            logger.error(f"[red]Failed to connect to Radarr: {e}[/red]")
            return False

    def get_all_movies(self) -> List[Dict[str, Any]]:
        """Get all movies from Radarr"""
        logger.info("[cyan]Fetching all movies from Radarr[/cyan]")

        try:
            movies = self.client.get_movie()
            logger.info(f"[green]Found {len(movies)} movies in Radarr[/green]")
            return movies
        except Exception as e:
            logger.error(f"[red]Failed to get movies from Radarr: {e}[/red]")
            return []

    def get_movie_by_tmdb_id(self, tmdb_id: str) -> Dict[str, Any]:
        """Get a specific movie by TMDB ID"""
        try:
            movies = self.client.get_movie()
            for movie in movies:
                if str(movie.get("tmdbId")) == str(tmdb_id):
                    return movie
            return {}
        except Exception as e:
            logger.error(f"[red]Failed to get movie by TMDB ID: {e}[/red]")
            return {}
