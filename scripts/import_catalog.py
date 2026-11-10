"""Import the verified public research datasets for the local website.

Run from the project root: python scripts/import_catalog.py
Uses only stdlib. Replaces only the previous integration sample or this importer’s
own datasets. Does not scrape ESPN or claim live injury coverage.
"""
from collections import defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import re
import time
import unicodedata
import urllib.request
import uuid
import supabase_client as db

BASE = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/"
MARKER = "courtside-catalog-v1"
fetched = {}


def load(tag, name):
    url = BASE + tag + "/" + name
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                raw = response.read()
                modified = response.headers.get("Last-Modified")
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise RuntimeError("SOURCE_DOWNLOAD_FAILED") from None
            time.sleep(2 ** attempt)
    fetched[name] = {"url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "http_last_modified": modified}
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))


def normalize(name):
    value = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return tuple(sorted(t for t in re.findall(r"[a-z0-9]+", value) if t not in ("jr", "sr", "ii", "iii", "iv")))


def require(ok, name):
    if not ok:
        raise RuntimeError(name)


def publish(kind, records, source, coverage, warnings):
    status, existing = db.api("GET", f"fantasy_data_snapshots?season=eq.2027&dataset_kind=eq.{kind}&select=payload,data_mode", role="public")
    require(status == 200, "read existing " + kind)
    require(all(r["data_mode"] == "imported" and
                (r["payload"].get("importer") == MARKER or r["payload"].get("proof_marker") == db.MARKER)
                for r in existing), "preserve unrelated " + kind + " datasets")
    fingerprint = content_hash(records, source, coverage, warnings)
    if existing and content_hash(existing[0]["payload"]["records"], source, existing[0]["payload"].get("coverage", {}), existing[0]["payload"].get("warnings", [])) == fingerprint:
        status, pointers = db.api("GET", f"fantasy_current_datasets?season=eq.2027&dataset_kind=eq.{kind}&select=snapshot_id")
        require(status == 200 and len(pointers) == 1, "read unchanged pointer")
        return {"snapshot_id": pointers[0]["snapshot_id"], "records": len(records), "changed": False}
    row = {
        "id": str(uuid.uuid4()), "dataset_kind": kind, "season": 2027,
        "source_url": source, "source_updated_at": None,
        "retrieved_at": datetime.now(timezone.utc).isoformat(), "data_mode": "imported",
        "payload": {"importer": MARKER, "content_hash": fingerprint, "records": records, "coverage": coverage, "warnings": warnings,
                    "attribution": {"source": "SportsDataverse / hoopR", "upstream": "ESPN and NBA Stats",
                                    "license": "CC BY 4.0 as declared by the producing repositories",
                                    "license_urls": ["https://github.com/sportsdataverse/hoopR-nba-data/blob/main/LICENSE.md",
                                                     "https://github.com/sportsdataverse/hoopR-nba-stats-data/blob/main/LICENSE.md"],
                                    "changes": "Normalized IDs/stat totals; selected latest injury report; separated TBD games. No artwork or commentary."}},
    }
    status, _ = db.api("POST", "fantasy_data_snapshots", row)
    require(status == 201, "stage " + kind)
    status, _ = db.publish(row["id"])
    require(status == 200, "publish " + kind)
    return {"snapshot_id": row["id"], "records": len(records), "changed": True}


def content_hash(records, source, coverage, warnings):
    body = {"records": sorted(records, key=lambda r: json.dumps(r, sort_keys=True)), "source": source, "coverage": coverage, "warnings": warnings}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_core(directory, totals, schedule, previous):
    require(len(directory) >= 300 and len(totals) >= 130 and len(schedule) >= 1000, "CORE_COVERAGE_TOO_SMALL")
    player_ids = [r["player_id"] for r in directory]
    require(len(player_ids) == len(set(player_ids)), "DUPLICATE_PLAYER_IDS")
    require(all(r["player_id"] in player_ids for r in totals), "UNMAPPED_STATISTICS")
    require(len({r["player_id"] for r in totals}) == len(totals), "DUPLICATE_STATISTICS")
    require(len({r["game_id"] for r in schedule}) == len(schedule), "DUPLICATE_GAMES")
    for row in totals:
        require(all(isinstance(v, int) and v >= 0 for k, v in row.items() if k != "player_id"), "INVALID_STAT_TOTAL")
        require(row["gp"] > 0 and row["three_pm"] <= row["fgm"] <= row["fga"] and row["ftm"] <= row["fta"], "INVALID_SHOOTING")
        require(row["pts"] == 2 * row["fgm"] + row["three_pm"] + row["ftm"], "INVALID_SCORING_IDENTITY")
    teams = set()
    for game in schedule:
        stamp = datetime.fromisoformat(game["starts_at"].replace("Z", "+00:00"))
        require(stamp.tzinfo is not None and 2026 <= stamp.year <= 2027, "INVALID_GAME_TIMESTAMP")
        require(game["home_team_id"] != game["away_team_id"], "INVALID_MATCHUP")
        teams.update((game["home_team_id"], game["away_team_id"]))
    require(len(teams) == 30, "INCOMPLETE_TEAM_COVERAGE")
    for kind, rows in [("players", directory), ("player_stats", totals), ("schedule", schedule)]:
        old = previous.get(kind, 0)
        require(not old or len(rows) >= old * 0.9, "UNEXPECTED_COVERAGE_DROP_" + kind.upper())


def main(core_only=False):
    fetched.clear()
    stats = load("espn_nba_player_season_stats", "player_season_stats_2027.csv")
    espn = load("espn_nba_rosters", "rosters_2027.csv")
    nba = load("nba_stats_rosters", "rosters_2027.csv")
    teams = load("nba_crosswalk", "nba_team_crosswalk_2027.csv")
    games = load("espn_nba_schedules", "nba_schedule_2027.csv")
    injuries = [] if core_only else load("nba_stats_injury_report", "injury_report_2027.csv")
    mappings = defaultdict(set)
    for season in (2027, 2026, 2025):
        for row in load("nba_crosswalk", f"nba_player_crosswalk_{season}.csv"):
            if row["espn_athlete_id"] and row["nba_player_id"]:
                mappings[row["espn_athlete_id"]].add(row["nba_player_id"])
    team_lookup = {r["espn_team_id"]: r for r in teams}
    nba_team = {r["nba_team_id"]: r for r in teams}
    require(len(team_lookup) == 30, "30-team directory")
    nba_names = defaultdict(list)
    for row in nba:
        nba_names[(row["team_id"], normalize(row["player"]))].append(row)
    nba_ids = {r["player_id"] for r in nba}
    nba_to_player = {}
    directory = {}
    for row in espn:
        eid = row["athlete_id"]
        team = team_lookup.get(row["team_id"], {})
        candidate = mappings.get(eid, set())
        matches = nba_names.get((team.get("nba_team_id"), normalize(row["display_name"])), [])
        nid = next(iter(candidate)) if len(candidate) == 1 and next(iter(candidate)) in nba_ids else None
        if nid and matches:
            require(any(m["player_id"] == nid for m in matches), "cross-source identity agreement")
        if not nid and len(candidate) <= 1 and len(matches) == 1:
            nid = matches[0]["player_id"]
        pid = "espn:" + eid
        if nid:
            require(nid not in nba_to_player, "unique provider alias")
            nba_to_player[nid] = pid
        directory[pid] = {"player_id": pid, "display_name": row["display_name"],
                          "team_id": row["team_id"], "team": row["team_abbreviation"],
                          "position": row["position_abbreviation"], "nba_id": nid}
    for row in nba:
        if row["player_id"] not in nba_to_player:
            pid = "nba:" + row["player_id"]
            team = nba_team.get(row["team_id"], {})
            directory[pid] = {"player_id": pid, "display_name": row["player"],
                              "team_id": team.get("espn_team_id", ""), "team": team.get("espn_abbreviation", "—"),
                              "position": row["position"], "nba_id": row["player_id"]}
            nba_to_player[row["player_id"]] = pid

    grouped = defaultdict(dict)
    for row in stats:
        if row["season"] != "2027":
            continue
        key = (row["category"], row["stat_name"])
        require(key not in grouped[row["athlete_id"]], "unique season-stat key") if key in grouped[row["athlete_id"]] else None
        grouped[row["athlete_id"]][key] = row
    totals, incomplete_stats = [], []
    for eid, data in grouped.items():
        gp_row = data.get(("averages", "gamesPlayed"))
        if not gp_row or int(gp_row["display_value"]) <= 0:
            continue
        pid = "espn:" + eid
        required = ['points','totalRebounds','assists','steals','blocks',
                    'fieldGoalsMade-fieldGoalsAttempted','freeThrowsMade-freeThrowsAttempted',
                    'threePointFieldGoalsMade-threePointFieldGoalsAttempted']
        if any(('totals', key) not in data for key in required):
            incomplete_stats.append(pid)
            continue
        record = {"player_id": pid, "gp": int(gp_row["display_value"])}
        for key, source in {"pts":"points", "reb":"totalRebounds", "ast":"assists", "stl":"steals", "blk":"blocks"}.items():
            record[key] = int(data[("totals", source)]["display_value"])
        for source, pair in [("fieldGoalsMade-fieldGoalsAttempted", ("fgm","fga")),
                             ("freeThrowsMade-freeThrowsAttempted", ("ftm","fta")),
                             ("threePointFieldGoalsMade-threePointFieldGoalsAttempted", ("three_pm","three_pa"))]:
            record[pair[0]], record[pair[1]] = map(int, data[("totals", source)]["display_value"].split("-"))
        if record["pts"] != 2*record["fgm"] + record["three_pm"] + record["ftm"]:
            raise ValueError("Scoring identity failed")
        totals.append(record)
        if pid not in directory:
            team = team_lookup.get(gp_row["team_id"], {})
            directory[pid] = {"player_id":pid, "display_name":gp_row["athlete_display_name"],
                              "team_id":gp_row["team_id"], "team":team.get("espn_abbreviation", "—"),
                              "position":gp_row["athlete_position_abbreviation"], "nba_id":None}
    require(len(totals) >= 130, "league-depth statistical coverage")

    schedule, unassigned = [], []
    seen_games = set()
    for row in games:
        if row["season_type"] != "2":
            continue
        require(row["game_id"] not in seen_games, "unique game ID") if row["game_id"] in seen_games else None
        seen_games.add(row["game_id"])
        if row["home_id"] not in team_lookup or row["away_id"] not in team_lookup:
            unassigned.append({"game_id":row["game_id"], "date":row["date"]})
            continue
        datetime.fromisoformat(row["date"].replace("Z", "+00:00"))
        schedule.append({"game_id":row["game_id"], "home_team_id":row["home_id"], "away_team_id":row["away_id"],
                         "starts_at":row["date"], "status":row["status_type_name"]})

    latest = max((r["report_datetime"] for r in injuries), default="")
    latest_rows = [r for r in injuries if r["report_datetime"] == latest]
    listings, unmatched = [], []
    for row in latest_rows:
        if not row["report_player_name"]:
            continue
        nid = row["person_id"]
        if not nid:
            matches = nba_names.get((row["team_id"], normalize(row["report_player_name"])), [])
            if len(matches) == 1:
                nid = matches[0]["player_id"]
        pid = nba_to_player.get(nid)
        if not pid:
            unmatched.append(row["report_player_name"])
            continue
        raw_status = row["current_status"].lower()
        status = raw_status if raw_status in ("available","probable","questionable","doubtful","out") else "unknown"
        key = "|".join((latest,row["game_date"],row["team_id"],pid,row["report_matchup"]))
        listings.append({"listing_id":hashlib.sha256(key.encode()).hexdigest()[:24], "player_id":pid,
                         "game_id":row["game_id"] or None, "game_date":row["game_date"], "status":status,
                         "report_local":latest, "report_timezone":"America/New_York"})
    require(len({r["listing_id"] for r in listings}) == len(listings), "unique injury listings")
    warning = ["Imported research snapshot. Underlying stat observation time is not provided."]
    status, previous = db.api("GET", "fantasy_data_snapshots?season=eq.2027&dataset_kind=in.(players,player_stats,schedule)&select=dataset_kind,record_count,payload,data_mode", role="public")
    require(status == 200, "READ_PREVIOUS_COVERAGE_FAILED")
    require(all(r["data_mode"] == "imported" and (r["payload"].get("importer") == MARKER or r["payload"].get("proof_marker") == db.MARKER) for r in previous), "UNRELATED_CORE_DATASET")
    validate_core(list(directory.values()), totals, schedule, {r["dataset_kind"]: r["record_count"] for r in previous})
    output = {}
    output["players"] = publish("players", sorted(directory.values(), key=lambda p:p["display_name"]),
                                BASE+"espn_nba_rosters/rosters_2027.csv", {"scope":"combined NBA/ESPN directory"}, warning)
    output["player_stats"] = publish("player_stats", totals, db.SOURCE,
                                     {"scope":"available player season totals", "season_type":"regular", "eligibility":"at least one played game and complete totals", "incomplete_player_ids":incomplete_stats}, warning)
    output["schedule"] = publish("schedule", schedule, BASE+"espn_nba_schedules/nba_schedule_2027.csv",
                                 {"unassigned_games":unassigned, "season_type":"regular"},
                                 ["Future schedule is provisional; unassigned games are excluded from team counts."])
    if not core_only:
        output["injuries"] = publish("injuries", listings, BASE+"nba_stats_injury_report/injury_report_2027.csv",
                                 {"report_local":latest, "report_timezone":"America/New_York", "unmatched":unmatched,
                                  "unsubmitted_teams": [r["team"] for r in latest_rows if not r["report_player_name"]]},
                                 ["Historical injury report, not live availability. Verify current status before trading."])
    output["source_files"] = fetched
    output["imported_at"] = datetime.now(timezone.utc).isoformat()
    path = db.ROOT / "reports" / "catalog-import.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({kind:record["records"] for kind,record in output.items() if isinstance(record,dict) and "records" in record}), flush=True)
    return output


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Import stopped: " + type(error).__name__ + ". No credentials logged.", flush=True)
        if isinstance(error, KeyError):
            print("Missing dataset field: " + str(error.args[0]), flush=True)
        raise SystemExit(1)
