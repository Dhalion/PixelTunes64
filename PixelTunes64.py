from SpotifyClient import SpotifyClient
from rich.console import Console
from rich.panel import Panel
from rich import box
import time
from os import getenv


class AppState:
    INIT = "init"
    READY = "ready"
    ERROR = "error"

class PixelTunes64:
    POLL_INTERVAL_DEFAULT = 5  # Sekunden

    def __init__(self):
        self.console = Console()
        self.state = AppState.INIT
        self.spotify = None
        self.error = None
        self.debug = getenv("DEBUG", "0").lower() in ("1", "true", "yes")
        self._init_spotify()

    def _init_spotify(self):
        try:
            self.spotify = SpotifyClient()
            self.state = AppState.READY
        except Exception as e:
            self.state = AppState.ERROR
            self.error = str(e)

    def run(self):
        last_track_id = None
        last_ends_at = None
        error_retries = 0
        MAX_RETRIES = 3
        premature_poll_next = False
        while True:
            if self.state == AppState.ERROR:
                if error_retries < MAX_RETRIES:
                    error_retries += 1
                    self.console.clear()
                    self.console.print(f"[yellow]⚠️ Fehler aufgetreten. Versuche Neustart {error_retries}/{MAX_RETRIES}...[/yellow]")
                    time.sleep(2)
                    self._init_spotify()
                    continue
                else:
                    self.console.clear()
                    self.console.print(f"[bold red]❌ Fehler bei der Spotify-Verbindung nach {MAX_RETRIES} Versuchen:[/bold red] [red]{self.error}[/red]")
                    break
            currently_playing = self.spotify.getCurrentlyPlaying()
            now = time.time()
            # Songwechsel, Wechsel zu Pause oder von Pause zu Song erkennen und sofort ausgeben
            if currently_playing and currently_playing.id != last_track_id:
                self.console.clear()
                self.console.print(Panel(str(currently_playing), title="[bold green]Aktueller Song[/bold green]", box=box.ROUNDED, border_style="cyan"))
                last_track_id = currently_playing.id
                last_ends_at = currently_playing.ends_at
            elif not currently_playing:
                self.console.clear()
                self.console.print(Panel("[yellow]⏸️  Gerade wird nichts abgespielt.[/yellow]", title="[bold yellow]Pause[/bold yellow]", box=box.ROUNDED, border_style="yellow"))
                last_track_id = None
                last_ends_at = None
            # Polling-Intervall bestimmen
            poll_interval = self.POLL_INTERVAL_DEFAULT
            premature_poll = False
            if currently_playing and currently_playing.ends_at:
                time_to_end = currently_playing.ends_at - now
                if 0 < time_to_end <= self.POLL_INTERVAL_DEFAULT:
                    poll_interval = max(0.1, time_to_end) # minimum 0.1 Sekunden
                    premature_poll = True
            # Debug-Ausgabe für Polling
            if self.debug:
                debug_msg = f"[dim][white]DEBUG: now={now:.2f}, poll_interval={poll_interval:.2f}, last_track_id={last_track_id}, ends_at={getattr(currently_playing, 'ends_at', None)}, premature_poll={premature_poll}[/white][/dim]"
                self.console.print(debug_msg)
            if premature_poll and self.debug:
                self.console.print("[dim][cyan]⏳ Warte auf Song-Ende für präzises Polling...[/cyan][/dim]")
            time.sleep(poll_interval)

