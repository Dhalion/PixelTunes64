# PixelTunes64

PixelTunes64 shows the cover art of the currently playing Spotify track on an RGB matrix.

## Installation

```bash
make install
```

The helper installs the required build tools on Fedora or Debian, creates `.venv/`, and then installs the Python dependencies there.

## Run

```bash
make run
```

`make run` uses the virtual environment created by `make install`.

## Matrix debug

To verify the matrix hardware without the app stack:

```bash
sudo .venv/bin/python debug_matrix_red.py
```

It fills the full 64x64 matrix with solid red and keeps it that way until you stop it.

## Configuration

Create a `.env` file in the project root:

```env
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://127.0.0.1:9090
SPOTIPY_MARKET=DE
MATRIX_DISPLAY_WIDTH=64
MATRIX_DISPLAY_HEIGHT=64
MATRIX_ROWS=64
MATRIX_COLS=64
MATRIX_CHAIN_LENGTH=1
MATRIX_PARALLEL=1
MATRIX_BRIGHTNESS=60
ALBUM_CACHE_DIR=.album-cache
POLL_INTERVAL_SECONDS=5
RESTART_DELAY_SECONDS=1
MAX_RESTART_DELAY_SECONDS=30
LOG_LEVEL=INFO
```

## Cache

Rendered cover art is stored as PNG files in `.album-cache/`. The cache key uses the Spotify album ID and the target size.

Set `LOG_LEVEL=DEBUG` if you want verbose Spotify and playback logs.
