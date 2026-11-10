"""Read-only localhost proof API; not the website UI.

Run: python scripts/serve_data_check.py
GET http://127.0.0.1:8765/api/health
GET http://127.0.0.1:8765/api/sample-trade
Only explicit routes exist: local files, environment settings and writes are not served.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import check_supabase as proof


def snapshot():
    status, current = proof.api(
        "GET", f"fantasy_current_datasets?dataset_kind=eq.player_stats&season=eq.{proof.SEASON}&select=snapshot_id", role="public")
    if status != 200 or len(current) != 1:
        raise ValueError("Dataset unavailable")
    status, records = proof.api(
        "GET", "fantasy_data_snapshots?id=eq." + current[0]["snapshot_id"]
        + "&select=payload,data_mode,season,retrieved_at,source_updated_at", role="public")
    if status != 200 or len(records) != 1:
        raise ValueError("Snapshot unavailable")
    return records[0]


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        encoded = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path not in ("/api/health", "/api/sample-trade"):
            self.respond(404, {"error": "Route not found"})
            return
        try:
            data = snapshot()
            if self.path == "/api/health":
                self.respond(200, {"database": "connected", "mode": data["data_mode"],
                                   "season": data["season"], "records": len(data["payload"]["records"])})
                return
            payload = data["payload"]
            players = payload["records"]
            if payload.get("proof_marker") != proof.MARKER or len(players) != 14:
                self.respond(409, {"error": "This endpoint requires the labeled integration sample"})
                return
            before, after = proof.aggregate(players[:13]), proof.aggregate(players[1:])
            self.respond(200, {
                "purpose": "Integration sample; not a live trade recommendation",
                "data_mode": data["data_mode"], "source_updated_at": data["source_updated_at"],
                "retrieved_at": data["retrieved_at"], "give": players[0]["display_name"],
                "receive": players[-1]["display_name"],
                "categories": {key: {"before": float(value) if value is not None else None,
                                      "after": float(after[key]) if after[key] is not None else None,
                                      "change": float(after[key] - value) if value is not None and after[key] is not None else None}
                               for key, value in before.items()},
                "warnings": payload["warnings"],
            })
        except Exception:
            self.respond(502, {"error": "Database read failed; no fallback data substituted"})

    def do_POST(self):
        self.respond(405, {"error": "Read-only diagnostic API"})

    do_PATCH = do_POST
    do_DELETE = do_POST
    do_PUT = do_POST

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Read-only data check: http://127.0.0.1:8765/api/health", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
