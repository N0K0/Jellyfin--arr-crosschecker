from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml


class JellyfinServiceConfig(BaseModel):
    url: str = Field(..., description="Jellyfin server URL")


class SonarrServiceConfig(BaseModel):
    url: str = Field(..., description="Sonarr server URL")


class RadarrServiceConfig(BaseModel):
    url: str = Field(..., description="Radarr server URL")


class ServiceURLConfig(BaseModel):
    jellyfin: JellyfinServiceConfig
    sonarr: SonarrServiceConfig
    radarr: RadarrServiceConfig


class JellyfinCredentials(BaseModel):
    username: str
    password: str


class SonarrCredentials(BaseModel):
    api_key: str


class RadarrCredentials(BaseModel):
    api_key: str


class CredentialsConfig(BaseModel):
    jellyfin: JellyfinCredentials
    sonarr: SonarrCredentials
    radarr: RadarrCredentials


class AppConfig:
    """Main application configuration that loads both URLs and credentials"""

    def __init__(
        self,
        config_path: Path = Path("config.yaml"),
        credentials_path: Path = Path("credentials.yaml")
    ):
        self.config_path = config_path
        self.credentials_path = credentials_path
        self.urls = self._load_urls()
        self.credentials = self._load_credentials()

    def _load_urls(self) -> ServiceURLConfig:
        """Load service URLs from config file"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}. "
                f"Copy config.yaml.example to config.yaml and update it."
            )

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        return ServiceURLConfig(**data)

    def _load_credentials(self) -> CredentialsConfig:
        """Load service credentials from credentials file"""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_path}. "
                f"Copy credentials.yaml.example to credentials.yaml and update it."
            )

        with open(self.credentials_path, "r") as f:
            data = yaml.safe_load(f)

        return CredentialsConfig(**data)
