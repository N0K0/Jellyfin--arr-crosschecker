#!/usr/bin/env python3
"""
Arr Cleaner - Cross-check watched content between Jellyfin and Sonarr/Radarr

This tool analyzes what content has been watched by users in Jellyfin and
cross-references it with what's available in Sonarr and Radarr.
"""
import asyncio
import threading
from pathlib import Path
import uvicorn
from src.config import AppConfig
from src.clients.jellyfin import JellyfinClient
from src.clients.radarr import RadarrClient
from src.clients.sonarr import SonarrClient
from src.service import ArrCleanerService
from src.web.app import app, set_report
from src.logger import logger, console


def run_web_server():
    """Run the FastAPI web server"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


def main():
    """Main entry point"""
    console.print("[bold cyan]Arr Cleaner - Watch Report Generator[/bold cyan]\n")

    try:
        # Load configuration
        logger.info("[cyan]Loading configuration...[/cyan]")
        config = AppConfig(
            config_path=Path("config.yaml"),
            credentials_path=Path("credentials.yaml")
        )

        # Initialize clients
        logger.info("[cyan]Initializing API clients...[/cyan]")

        jellyfin_client = JellyfinClient(
            base_url=config.urls.jellyfin.url,
            username=config.credentials.jellyfin.username,
            password=config.credentials.jellyfin.password
        )

        radarr_client = RadarrClient(
            base_url=config.urls.radarr.url,
            api_key=config.credentials.radarr.api_key
        )

        sonarr_client = SonarrClient(
            base_url=config.urls.sonarr.url,
            api_key=config.credentials.sonarr.api_key
        )

        # Create service
        service = ArrCleanerService(
            jellyfin_client=jellyfin_client,
            radarr_client=radarr_client,
            sonarr_client=sonarr_client,
            jellyfin_url=config.urls.jellyfin.url,
            radarr_url=config.urls.radarr.url,
            sonarr_url=config.urls.sonarr.url
        )

        # Collect data
        report = service.collect_data()

        # Load report into web app
        set_report(report)

        # Print summary
        console.print("\n[bold green]Report Summary:[/bold green]")
        console.print(f"  Users: {len(report.users)}")
        console.print(f"  Movies watched by all: {len(report.movies_watched_by_all)}")
        console.print(f"  Movies watched by some: {len(report.movies_watched_by_some)}")
        console.print(f"  Series fully watched by all: {len(report.series_fully_watched_by_all)}")
        console.print(f"  Series fully watched by some: {len(report.series_fully_watched_by_some)}")
        console.print(f"  Series partially watched by all: {len(report.series_partially_watched_by_all)}")
        console.print(f"  Series partially watched by some: {len(report.series_partially_watched_by_some)}")

        # Clean up
        jellyfin_client.close()

        # Start web server
        console.print("\n[bold cyan]Starting web server...[/bold cyan]")
        console.print("[bold green]Open your browser to: http://localhost:8000[/bold green]\n")
        console.print("[yellow]Press Ctrl+C to stop the server[/yellow]\n")

        run_web_server()

    except FileNotFoundError as e:
        logger.error(f"[red]{e}[/red]")
        console.print("\n[yellow]Please create the required configuration files.[/yellow]")
        return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        return 0

    except Exception as e:
        logger.exception(f"[red]An error occurred: {e}[/red]")
        return 1


if __name__ == "__main__":
    exit(main())
