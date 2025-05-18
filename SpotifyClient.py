from rich.console import Console
from rich.markup import escape
import spotipy
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class CurrentlyPlaying:
    id: str
    artist: str
    title: str
    album_cover_64: Optional[str]
    ends_at: Optional[float]

    def __str__(self):
        cover = f"[link={self.album_cover_64}]🖼️[/link]" if self.album_cover_64 else ""
        end_str = ""
        stamp_str = ""
        if self.ends_at:
            import datetime
            dt = datetime.datetime.fromtimestamp(self.ends_at)
            end_str = f"[dim]| endet um: {dt:%H:%M:%S}[/dim]"
            stamp_str = f"[dim]| timestamp: {self.ends_at:.0f}[/dim]"
        return f"[bold cyan]🎵 Now Playing:[/bold cyan] [magenta]{self.title}[/magenta] [dim]von[/dim] [yellow]{self.artist}[/yellow] {cover} {end_str} {stamp_str}"

class SpotifyClient:
    CALLBACK_URL = "http://127.0.0.1:9090"
    SCOPES = [
        "user-library-read",
        "user-read-currently-playing",
        "user-read-playback-state",
    ]

    def __init__(self):
        self.console = Console()
        cache_path = os.getenv("SPOTIPY_CACHE_PATH", ".cache")
        if not os.path.exists(cache_path):
            self.console.print("[yellow]⚠️  Kein Spotify-Token gefunden. Starte Authentifizierung...[/yellow]")
        try:
            authManager = spotipy.SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=self.CALLBACK_URL,
                scope=" ".join(self.SCOPES),
                cache_path=cache_path
            )
            self.client = spotipy.Spotify(auth_manager=authManager)
            # Testverbindung
            self.client.current_user()
            self.console.print("[green]✔ Spotify Authentifizierung erfolgreich![/green]")
        except Exception as e:
            self.console.print(f"[bold red]❌ Spotify Authentifizierung fehlgeschlagen:[/bold red] [red]{escape(str(e))}[/red]")
            raise RuntimeError(f"Spotify Authentifizierung fehlgeschlagen: {e}")

    def getCurrentlyPlaying(self) -> Optional[CurrentlyPlaying]:
        try:
            state = self.client.current_playback('DE')
            if state and state.get('item') and state.get('is_playing'):
                item = state['item']
                name = item['name']
                artists = ', '.join([artist['name'] for artist in item['artists']])
                track_id = item['id']
                album_cover_64 = None
                if item.get('album') and item['album'].get('images'):
                    images = item['album']['images']
                    album_cover_64 = next((img['url'] for img in images if img['width'] == 64), None)
                    if not album_cover_64 and images:
                        album_cover_64 = images[-1]['url']
                # Zeitstempel berechnen
                ends_at = None
                if state.get('progress_ms') is not None and item.get('duration_ms') is not None:
                    import time
                    now = time.time()
                    ms_left = item['duration_ms'] - state['progress_ms']
                    ends_at = now + ms_left / 1000.0
                return CurrentlyPlaying(
                    id=track_id,
                    artist=artists,
                    title=name,
                    album_cover_64=album_cover_64,
                    ends_at=ends_at
                )
            else:
                return None
        except Exception as e:
            self.console.print(f"[bold red]❌ Fehler beim Abrufen des aktuellen Tracks:[/bold red] [red]{escape(str(e))}[/red]")
            return None

