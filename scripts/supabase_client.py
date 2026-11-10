"""Backend-only REST client; credentials stay in environment variables or .env.local."""
from pathlib import Path
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MARKER = "nba-roster-proof-v1"
SOURCE = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_nba_player_season_stats/player_season_stats_2027.csv"


def settings():
    values = {}
    path = ROOT / ".env.local"
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    values.update(os.environ)
    return values


def api(method, path, body=None, role="backend"):
    values = settings()
    url = values.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
    host = urllib.parse.urlparse(url)
    if host.scheme != "https" or not (host.hostname or "").endswith(".supabase.co"):
        raise RuntimeError("INVALID_DATABASE_CONFIGURATION")
    key = values.get("SUPABASE_SECRET_KEY" if role == "backend" else "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
    if not key:
        raise RuntimeError("MISSING_DATABASE_CONFIGURATION")
    headers = {"apikey": key, "Accept": "application/json", "Content-Type": "application/json"}
    for attempt in range(3):
        request = urllib.request.Request(url + "/rest/v1/" + path, method=method, headers=headers,
                                         data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            if method != "GET" and error.code in (429, 500, 502, 503, 504):
                raise RuntimeError("DATABASE_CONNECTION_FAILED") from None
            if method == "GET" and error.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            # Never include provider response bodies, request URLs or headers in errors.
            return error.code, None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if method != "GET" or attempt == 2:
                raise RuntimeError("DATABASE_CONNECTION_FAILED") from None
            time.sleep(2 ** attempt)


def publish(snapshot_id):
    return api("POST", "rpc/fantasy_publish_snapshot", {"p_snapshot_id": snapshot_id})
