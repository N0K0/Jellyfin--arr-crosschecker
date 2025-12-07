from typing import List, Dict, Any
from collections import defaultdict
from src.clients.jellyfin import JellyfinClient
from src.clients.radarr import RadarrClient
from src.clients.sonarr import SonarrClient
from src.models import MovieInfo, SeriesInfo, UserWatchData, Report
from src.logger import logger


class ArrCleanerService:
    """Main service for coordinating data collection and analysis"""

    def __init__(
        self,
        jellyfin_client: JellyfinClient,
        radarr_client: RadarrClient,
        sonarr_client: SonarrClient,
        jellyfin_url: str = None,
        radarr_url: str = None,
        sonarr_url: str = None
    ):
        self.jellyfin = jellyfin_client
        self.radarr = radarr_client
        self.sonarr = sonarr_client
        self.jellyfin_url = jellyfin_url
        self.radarr_url = radarr_url
        self.sonarr_url = sonarr_url

    def collect_data(self) -> Report:
        """Collect all data and generate a comprehensive report"""
        logger.info("[bold cyan]Starting data collection...[/bold cyan]")

        # Authenticate with Jellyfin
        if not self.jellyfin.authenticate():
            logger.error("[red]Failed to authenticate with Jellyfin[/red]")
            return Report()

        # Test Radarr and Sonarr connections
        self.radarr.test_connection()
        self.sonarr.test_connection()

        # Get all users from Jellyfin
        jellyfin_users = self.jellyfin.get_users()

        # Get Radarr and Sonarr data
        radarr_movies = self.radarr.get_all_movies()
        sonarr_series = self.sonarr.get_all_series()

        # Build lookup dictionaries
        radarr_tmdb_lookup = {
            str(movie.get("tmdbId")): movie
            for movie in radarr_movies
            if movie.get("tmdbId")
        }

        sonarr_tvdb_lookup = {
            str(series.get("tvdbId")): series
            for series in sonarr_series
            if series.get("tvdbId")
        }

        # Collect watch data for each user
        users_data = []
        for user in jellyfin_users:
            user_id = user["Id"]
            username = user["Name"]

            logger.info(f"[cyan]Processing user: {username}[/cyan]")

            user_data = UserWatchData(user_id=user_id, username=username)

            # Get watched movies
            watched_movies = self.jellyfin.get_watched_movies(user_id)
            for movie in watched_movies:
                movie_info = self._parse_movie(movie, radarr_tmdb_lookup)
                user_data.watched_movies.append(movie_info)

            # Get watched series
            watched_series = self.jellyfin.get_watched_series(user_id)
            for series in watched_series:
                series_info = self._parse_series(series, user_id, sonarr_tvdb_lookup)
                if series_info:
                    user_data.watched_series.append(series_info)

            users_data.append(user_data)

        # Generate report with cross-checking
        report = self._generate_report(users_data)

        logger.info("[bold green]Data collection complete![/bold green]")
        return report

    def _parse_movie(
        self,
        movie: Dict[str, Any],
        radarr_lookup: Dict[str, Any]
    ) -> MovieInfo:
        """Parse Jellyfin movie data into MovieInfo"""
        provider_ids = movie.get("ProviderIds", {})
        tmdb_id = provider_ids.get("Tmdb")
        imdb_id = provider_ids.get("Imdb")

        radarr_movie = radarr_lookup.get(str(tmdb_id)) if tmdb_id else None
        in_radarr = radarr_movie is not None
        radarr_id = radarr_movie.get("id") if radarr_movie else None

        return MovieInfo(
            title=movie.get("Name", "Unknown"),
            year=movie.get("ProductionYear"),
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            path=movie.get("Path"),
            in_radarr=in_radarr,
            radarr_id=radarr_id,
            jellyfin_id=movie.get("Id")
        )

    def _parse_series(
        self,
        series: Dict[str, Any],
        user_id: str,
        sonarr_lookup: Dict[str, Any]
    ) -> SeriesInfo:
        """Parse Jellyfin series data into SeriesInfo"""
        provider_ids = series.get("ProviderIds", {})
        tvdb_id = provider_ids.get("Tvdb")
        imdb_id = provider_ids.get("Imdb")

        sonarr_series = sonarr_lookup.get(str(tvdb_id)) if tvdb_id else None
        in_sonarr = sonarr_series is not None
        sonarr_id = sonarr_series.get("id") if sonarr_series else None
        sonarr_title_slug = sonarr_series.get("titleSlug") if sonarr_series else None

        # Get watch status
        series_id = series.get("Id")
        is_fully_watched, watched_count, total_count = self.jellyfin.is_series_fully_watched(
            series_id, user_id
        )

        # Only include series that have been watched (at least partially)
        if watched_count == 0:
            return None

        return SeriesInfo(
            title=series.get("Name", "Unknown"),
            year=series.get("ProductionYear"),
            tvdb_id=tvdb_id,
            imdb_id=imdb_id,
            path=series.get("Path"),
            in_sonarr=in_sonarr,
            sonarr_id=sonarr_id,
            sonarr_title_slug=sonarr_title_slug,
            jellyfin_id=series_id,
            total_episodes=total_count,
            watched_episodes=watched_count,
            is_fully_watched=is_fully_watched
        )

    def _generate_report(self, users_data: List[UserWatchData]) -> Report:
        """Generate a report with cross-checking logic"""
        logger.info("[cyan]Generating report...[/cyan]")

        report = Report(
            users=users_data,
            jellyfin_url=self.jellyfin_url,
            radarr_url=self.radarr_url,
            sonarr_url=self.sonarr_url
        )

        if not users_data:
            return report

        # Track movies by title+year for cross-user comparison
        movie_watchers: Dict[str, List[str]] = defaultdict(list)
        movie_data: Dict[str, MovieInfo] = {}

        for user_data in users_data:
            for movie in user_data.watched_movies:
                key = f"{movie.title}_{movie.year}"
                movie_watchers[key].append(user_data.username)
                movie_data[key] = movie

        # Track series by title+year for cross-user comparison
        series_watchers_full: Dict[str, List[str]] = defaultdict(list)
        series_watchers_partial: Dict[str, List[str]] = defaultdict(list)
        series_data: Dict[str, SeriesInfo] = {}

        for user_data in users_data:
            for series in user_data.watched_series:
                key = f"{series.title}_{series.year}"
                if series.is_fully_watched:
                    series_watchers_full[key].append(user_data.username)
                else:
                    series_watchers_partial[key].append(user_data.username)
                series_data[key] = series

        total_users = len(users_data)

        # Categorize movies
        for key, watchers in movie_watchers.items():
            movie = movie_data[key]
            movie.watched_by_users = watchers
            if len(watchers) == total_users:
                report.movies_watched_by_all.append(movie)
            else:
                report.movies_watched_by_some.append(movie)

        # Categorize fully watched series
        for key, watchers in series_watchers_full.items():
            series = series_data[key]
            series.watched_by_users = watchers
            if len(watchers) == total_users:
                report.series_fully_watched_by_all.append(series)
            else:
                report.series_fully_watched_by_some.append(series)

        # Categorize partially watched series
        for key, watchers in series_watchers_partial.items():
            series = series_data[key]
            series.watched_by_users = watchers
            if len(watchers) == total_users:
                report.series_partially_watched_by_all.append(series)
            else:
                report.series_partially_watched_by_some.append(series)

        logger.info(
            f"[green]Report generated: "
            f"{len(report.movies_watched_by_all)} movies watched by all, "
            f"{len(report.series_fully_watched_by_all)} series fully watched by all[/green]"
        )

        return report
