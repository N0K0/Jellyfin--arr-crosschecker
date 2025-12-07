from typing import List, Dict, Optional
from pydantic import BaseModel


class MovieInfo(BaseModel):
    """Information about a movie"""
    title: str
    year: Optional[int] = None
    tmdb_id: Optional[str] = None
    imdb_id: Optional[str] = None
    path: Optional[str] = None
    in_radarr: bool = False
    radarr_id: Optional[int] = None
    jellyfin_id: Optional[str] = None
    watched_by_users: List[str] = []


class SeriesInfo(BaseModel):
    """Information about a series"""
    title: str
    year: Optional[int] = None
    tvdb_id: Optional[str] = None
    imdb_id: Optional[str] = None
    path: Optional[str] = None
    in_sonarr: bool = False
    sonarr_id: Optional[int] = None
    sonarr_title_slug: Optional[str] = None
    jellyfin_id: Optional[str] = None
    total_episodes: int = 0
    watched_episodes: int = 0
    is_fully_watched: bool = False
    watched_by_users: List[str] = []


class UserWatchData(BaseModel):
    """Watch data for a specific user"""
    user_id: str
    username: str
    watched_movies: List[MovieInfo] = []
    watched_series: List[SeriesInfo] = []


class Report(BaseModel):
    """Complete report of watched content"""
    users: List[UserWatchData] = []
    movies_watched_by_all: List[MovieInfo] = []
    movies_watched_by_some: List[MovieInfo] = []
    series_fully_watched_by_all: List[SeriesInfo] = []
    series_fully_watched_by_some: List[SeriesInfo] = []
    series_partially_watched_by_all: List[SeriesInfo] = []
    series_partially_watched_by_some: List[SeriesInfo] = []
    jellyfin_url: Optional[str] = None
    radarr_url: Optional[str] = None
    sonarr_url: Optional[str] = None
