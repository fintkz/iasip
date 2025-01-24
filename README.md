# IASIP Downloader
Found DVD extras of Always Sunny on the Internet Archive. Instead of spending 10 mins clicking each link, I spent an hour making this automation script ¯\\_(ツ)_/¯

Downloads seasons from `archive.org/download/its_always_sunny_complete_archive` to `/Users/fintkz/Movies/tv/iasip/{season_number}/`

Checks disk space, uses progress bars, downloads in parallel. You know, the works.

## Usage
```bash
uv sync
uv run -m playwright install
uv run download.py
