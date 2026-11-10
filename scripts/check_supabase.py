"""Run the authorized hosted data-pipeline proof; never print environment secrets.

Run from the repository root: python scripts/check_supabase.py
Uses only the Python standard library. Keeps two valid, labeled imported snapshots
and one sanitized refresh log. Deletes only invalid staging rows created by this run.
Refuses to replace an existing dataset unless it belongs to this same proof.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
import csv
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "supabase-check.json"
SEASON = 2027
MARKER = "nba-roster-proof-v1"
SOURCE = (
    "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/"
    "espn_nba_player_season_stats/player_season_stats_2027.csv"
)
RESULT = {"started_at": datetime.now(timezone.utc).isoformat(), "checks": []}
CREATED = []
settings = {}
for raw in (ROOT / ".env.local").read_text(encoding="utf-8-sig").splitlines():
    raw = raw.strip()
    if raw and not raw.startswith("#") and "=" in raw:
        name, value = raw.split("=", 1)
        settings[name.strip()] = value.strip().strip('"').strip("'")
URL = settings["NEXT_PUBLIC_SUPABASE_URL"].rstrip("/")
host = urllib.parse.urlparse(URL)
if host.scheme != "https" or not host.hostname.endswith(".supabase.co"):
    raise SystemExit("Expected an HTTPS Supabase project URL.")
KEYS = {
    "public": settings["NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"],
    "backend": settings["SUPABASE_SECRET_KEY"],
}


def api(method, path, body=None, role="backend", represent=False):
    headers = {"Accept": "application/json"}
    if role in KEYS:
        headers["apikey"] = KEYS[role]
    if body is not None:
        headers["Content-Type"] = "application/json"
    if represent:
        headers["Prefer"] = "return=representation"
    request = urllib.request.Request(
        URL + "/rest/v1/" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        # Do not print response bodies: they may contain untrusted or private text.
        try:
            raw = json.loads(error.read())
        except (ValueError, UnicodeError):
            raw = {}
        code = raw.get("code")
        allowed = (
            "INVALID_SHOOTING_OR_GAMES", "DUPLICATE_RECORD_ID",
            "OLDER_SNAPSHOT_REJECTED", "UNASSIGNED_OR_INVALID_GAME",
        )
        return error.code, {
            "code": code if isinstance(code, str) and code.isalnum() else None,
            "known_error": raw.get("message") if raw.get("message") in allowed else None,
        }


def check(ok, label):
    RESULT["checks"].append({"name": label, "passed": bool(ok)})
    print(("PASS " if ok else "FAIL ") + label, flush=True)
    if not ok:
        raise RuntimeError(label)


def rows(path, role="backend"):
    status, body = api("GET", path, role=role)
    check(status == 200 and isinstance(body, list), "read " + path.split("?")[0] + " as " + role)
    return body


def current():
    status, body = api("GET", f"fantasy_current_datasets?dataset_kind=eq.player_stats&season=eq.{SEASON}&select=snapshot_id")
    check(status == 200 and isinstance(body, list), "read current-version pointer")
    return body[0]["snapshot_id"] if body else None


def stage(records, payload_extra, observed, retrieved=None, kind="player_stats"):
    snapshot_id = str(uuid.uuid4())
    row = {
        "id": snapshot_id, "dataset_kind": kind, "season": SEASON,
        "source_url": SOURCE, "source_updated_at": observed,
        "retrieved_at": retrieved or datetime.now(timezone.utc).isoformat(),
        "data_mode": "imported", "payload": {**payload_extra, "records": records},
    }
    status, _ = api("POST", "fantasy_data_snapshots", row)
    check(status == 201, "backend stages " + kind + " snapshot")
    CREATED.append(snapshot_id)
    return snapshot_id


def publish(snapshot_id):
    return api("POST", "rpc/fantasy_publish_snapshot", {"p_snapshot_id": snapshot_id})


def load_players():
    with urllib.request.urlopen(SOURCE, timeout=40) as response:
        raw = response.read()
    source_rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    grouped = defaultdict(dict)
    for row in source_rows:
        if row["season"] != str(SEASON):
            continue
        key = (row["category"], row["stat_name"])
        if key in grouped[row["athlete_id"]]:
            raise RuntimeError("Duplicate source stat key: importer needs explicit team-stint handling")
        grouped[row["athlete_id"]][key] = row
    valid = []
    for athlete_id, data in grouped.items():
        gp_row = data.get(("averages", "gamesPlayed"))
        if not gp_row or int(gp_row["display_value"]) < 5:
            continue
        player = {
            "player_id": "espn:" + athlete_id,
            "display_name": gp_row["athlete_display_name"],
            "gp": int(gp_row["display_value"]),
        }
        for target, source in {"pts": "points", "reb": "totalRebounds", "ast": "assists", "stl": "steals", "blk": "blocks"}.items():
            player[target] = int(data[("totals", source)]["display_value"])
        for key, targets in [
            ("fieldGoalsMade-fieldGoalsAttempted", ("fgm", "fga")),
            ("freeThrowsMade-freeThrowsAttempted", ("ftm", "fta")),
            ("threePointFieldGoalsMade-threePointFieldGoalsAttempted", ("three_pm", "three_pa")),
        ]:
            made, attempted = map(int, data[("totals", key)]["display_value"].split("-"))
            player[targets[0]], player[targets[1]] = made, attempted
        if player["pts"] != 2 * player["fgm"] + player["three_pm"] + player["ftm"]:
            raise ValueError("Source scoring identity does not reconcile")
        valid.append(player)
    check(bool(valid), "source scoring identities reconcile across the eligible pool")
    lookup = {p["player_id"]: p for p in valid}
    outgoing, incoming = lookup["espn:3945274"], lookup["espn:3032977"]
    others = sorted((p for p in valid if p not in (outgoing, incoming)), key=lambda p: p["display_name"])[:12]
    check(len(others) == 12, "source supplies a complete 13-player test roster")
    selected = [outgoing, *others, incoming]
    RESULT["source"] = {"url": SOURCE, "bytes": len(raw), "season": SEASON, "eligible_players": len(valid), "selected_players": len(selected)}
    # Underlying stat observation time is not provided in the CSV. Keep it null.
    return selected, {p["player_id"]: grouped[p["player_id"].split(":")[1]] for p in selected}


def aggregate(roster):
    totals = {key: sum((Fraction(p[key], p["gp"]) for p in roster), Fraction())
              for key in ["pts", "reb", "ast", "stl", "blk", "three_pm", "fgm", "fga", "ftm", "fta"]}
    result = {key: totals[key] for key in ["pts", "reb", "ast", "stl", "blk", "three_pm"]}
    result["fg_pct"] = totals["fgm"] / totals["fga"] * 100 if totals["fga"] else None
    result["ft_pct"] = totals["ftm"] / totals["fta"] * 100 if totals["fta"] else None
    return result


def main():
    started = time.monotonic()
    for table in ["fantasy_data_snapshots", "fantasy_current_datasets", "fantasy_refresh_runs"]:
        rows(table + "?select=*&limit=1")
    rows("fantasy_current_datasets?select=*&limit=1", "public")
    status, _ = api("GET", "fantasy_current_datasets?select=*&limit=1", role="none")
    check(status in (401, 403), "requests without an API key are denied")
    status, _ = api("GET", "fantasy_refresh_runs?select=id&limit=1", role="public")
    check(status in (401, 403), "public cannot read refresh logs")

    existing = current()
    if existing:
        prior = rows("fantasy_data_snapshots?id=eq." + existing + "&select=payload,data_mode")[0]
        check(prior["data_mode"] == "imported" and prior["payload"].get("proof_marker") == MARKER,
              "existing data belongs to this repeatable proof; preserve unrelated datasets")

    players, source_rows = load_players()
    payload = {
        "proof_marker": MARKER,
        "coverage": {"scope": "14-player integration sample", "complete_league": False, "season_type": "regular"},
        "warnings": ["Integration sample, not a complete live dataset.", "Underlying observation time is unknown; retrieval time does not establish freshness."],
        "attribution": {"authors": "hoopR.nba authors / SportsDataverse", "producer_license": "https://github.com/sportsdataverse/hoopR-nba-data/blob/main/LICENSE.md", "upstream": "ESPN", "transformations": "Ending-year filter, 14-player sample, normalized integer totals; no proprietary commentary or artwork."},
    }
    first = stage(players, payload, None)
    status, hidden = api("GET", "fantasy_data_snapshots?id=eq." + first + "&select=id", role="public")
    check(status == 200 and hidden == [], "public cannot see unpublished staging snapshot")
    status, _ = api("POST", "rpc/fantasy_publish_snapshot", {"p_snapshot_id": first}, role="public")
    check(status in (401, 403), "public cannot execute publication function")
    status, published = publish(first)
    check(status == 200 and published == first, "backend publishes sample atomically")
    visible = rows("fantasy_data_snapshots?id=eq." + first + "&select=id,payload,data_mode,record_count", "public")
    check(len(visible) == 1 and visible[0]["record_count"] == 14 and visible[0]["data_mode"] == "imported", "public reads explicitly labeled imported sample")
    stored = visible[0]["payload"]["records"]
    check(stored == players, "all imported stat fields survive database round-trip")
    denied_id = str(uuid.uuid4())
    status, _ = api("POST", "fantasy_data_snapshots", {
        "id": denied_id, "dataset_kind": "player_stats", "season": SEASON,
        "source_url": SOURCE, "data_mode": "imported", "payload": {"records": players[:1]},
    }, role="public")
    if status == 201:
        api("DELETE", "fantasy_data_snapshots?id=eq." + denied_id)
    check(status in (401, 403), "public cannot insert snapshots")
    status, _ = api("PATCH", f"fantasy_current_datasets?dataset_kind=eq.player_stats&season=eq.{SEASON}",
                    {"snapshot_id": first}, role="public")
    check(status in (401, 403), "public cannot change current-version pointers")

    before, after = aggregate(stored[:13]), aggregate(stored[1:])
    expected_delta = {}
    stat_names = {"pts": "points", "reb": "totalRebounds", "ast": "assists", "stl": "steals", "blk": "blocks"}
    for key, name in stat_names.items():
        outgoing = source_rows[players[0]["player_id"]]
        incoming = source_rows[players[-1]["player_id"]]
        expected_delta[key] = Fraction(int(incoming[("totals", name)]["display_value"]), players[-1]["gp"]) - Fraction(int(outgoing[("totals", name)]["display_value"]), players[0]["gp"])
        check(after[key] - before[key] == expected_delta[key], "trade delta agrees with source totals: " + key)
    for prefix, source_key in [("fg", "fieldGoalsMade-fieldGoalsAttempted"), ("ft", "freeThrowsMade-freeThrowsAttempted")]:
        for label, team, result in [("before", players[:13], before), ("after", players[1:], after)]:
            pairs = [tuple(map(int, source_rows[p["player_id"]][("totals", source_key)]["display_value"].split("-"))) for p in team]
            made = sum((Fraction(pair[0], p["gp"]) for pair, p in zip(pairs, team)), Fraction())
            attempted = sum((Fraction(pair[1], p["gp"]) for pair, p in zip(pairs, team)), Fraction())
            check(result[prefix + "_pct"] == made / attempted * 100, "volume-weighted " + prefix + "% reconciles " + label)
    check(after["three_pm"] - before["three_pm"] == Fraction(stored[-1]["three_pm"], stored[-1]["gp"]) - Fraction(stored[0]["three_pm"], stored[0]["gp"]), "three-pointer trade delta reconciles")
    RESULT["trade"] = {"roster": [p["display_name"] for p in players[:13]], "give": players[0]["display_name"], "receive": players[-1]["display_name"], "before": {k:float(v) if v is not None else None for k,v in before.items()}, "after": {k:float(v) if v is not None else None for k,v in after.items()}}

    bad = stage([{**players[0], "fgm": players[0]["fga"] + 1}], payload, None)
    status, error = publish(bad)
    check(status == 400 and error.get("known_error") == "INVALID_SHOOTING_OR_GAMES", "database rejects invalid shooting import")
    check(current() == first, "failed import preserves last valid current snapshot")
    status, _ = api("PATCH", "fantasy_data_snapshots?id=eq." + bad, {"data_mode": "demo"}, role="public")
    check(status in (401, 403), "public cannot update snapshots")
    status, _ = api("DELETE", "fantasy_data_snapshots?id=eq." + bad, role="public")
    check(status in (401, 403), "public cannot delete snapshots")
    status, _ = api("POST", "fantasy_refresh_runs", {"dataset_kind":"player_stats", "season":SEASON}, role="public")
    check(status in (401, 403), "public cannot insert refresh records")

    duplicate = stage([players[0], players[0]], payload, None)
    status, error = publish(duplicate)
    check(status == 400 and error.get("known_error") == "DUPLICATE_RECORD_ID", "database rejects duplicate IDs")
    second = stage(players, payload, None)
    status, _ = publish(second)
    check(status == 200 and current() == second, "new valid import replaces current snapshot")
    status, old_visible = api("GET", "fantasy_data_snapshots?id=eq." + first + "&select=id", role="public")
    check(status == 200 and old_visible == [], "superseded version is hidden from public reads")
    older = stage(players, payload, None, retrieved=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat())
    status, error = publish(older)
    check(status == 400 and error.get("known_error") == "OLDER_SNAPSHOT_REJECTED", "older retrieval cannot overwrite a newer snapshot")
    check(current() == second, "all failed imports leave the last valid dataset usable")

    log_id = str(uuid.uuid4())
    status, _ = api("POST", "fantasy_refresh_runs", {"id":log_id, "dataset_kind":"player_stats", "season":SEASON, "status":"failed", "snapshot_id":bad, "finished_at":datetime.now(timezone.utc).isoformat(), "error_code":"TEST_INVALID_SHOOTING"})
    check(status == 201, "backend records sanitized failed refresh")
    # Remove only this run's unpublished test rows; keep the two valid snapshots.
    status, _ = api("PATCH", "fantasy_refresh_runs?id=eq." + log_id, {"snapshot_id":None})
    check(status == 204, "test log no longer references staging cleanup rows")
    for snapshot_id in [bad, duplicate, older]:
        status, _ = api("DELETE", "fantasy_data_snapshots?id=eq." + snapshot_id)
        check(status == 204, "clean up own invalid staging snapshot")
    RESULT["published_sample_id"] = second
    RESULT["elapsed_seconds"] = round(time.monotonic()-started, 2)
    RESULT["limitations"] = ["Localhost-to-hosted-Supabase only; no Vercel or Supabase Edge Function execution tested.", "No user-login session test was performed; anonymous publishable-key access was tested.", "14-player imported sample, not a live league-wide refresh.", "Injury automation and public-release data rights remain separate unresolved checks."]


if __name__ == "__main__":
    success = False
    try:
        main()
        success = True
    except Exception as error:
        # A safe error label, not a traceback or credentials-bearing HTTP request.
        RESULT["failure_type"] = type(error).__name__
        print("FAILED: see the recorded check names; no credentials logged.", flush=True)
    finally:
        RESULT["success"] = success
        RESULT["finished_at"] = datetime.now(timezone.utc).isoformat()
        RESULT["created_snapshot_ids"] = CREATED
        REPORT.parent.mkdir(exist_ok=True)
        REPORT.write_text(json.dumps(RESULT, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if success else 1)
