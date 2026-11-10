"""Run one monitored core refresh, locally or in GitHub Actions. No third-party dependencies."""
from datetime import datetime, timezone
import json
import os
import time
import uuid
import import_catalog as catalog
import supabase_client as db

KINDS = ("players", "player_stats", "schedule")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def run():
    report = {"started_at": utcnow(), "status": "running", "season": 2027, "attempts": 0,
              "scope": list(KINDS), "injuries": "Archived listings unchanged; current injuries are not imported."}
    log_ids = {}
    try:
        for kind in KINDS:
            run_id = str(uuid.uuid4())
            status, _ = db.api("POST", "fantasy_refresh_runs", {"id": run_id, "dataset_kind": kind, "season": 2027, "status": "running"})
            if status != 201:
                raise RuntimeError("REFRESH_LOG_START_FAILED")
            log_ids[kind] = run_id
        for attempt in range(3):
            report["attempts"] = attempt + 1
            try:
                output = catalog.main(core_only=True)
                report["datasets"] = {kind: output[kind] for kind in KINDS}
                report["source_files"] = output["source_files"]
                break
            except RuntimeError as error:
                if str(error) not in ("SOURCE_DOWNLOAD_FAILED", "DATABASE_CONNECTION_FAILED") or attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
        report["status"] = "succeeded"
    except Exception as error:
        report["status"] = "failed"
        code = str(error) if isinstance(error, RuntimeError) else "IMPORT_VALIDATION_FAILED"
        report["error_code"] = code if code.isupper() and code.replace("_", "").isalnum() and len(code) <= 80 else "IMPORT_VALIDATION_FAILED"
        report["note"] = "Each dataset publishes separately. On failure, some kinds may already be updated; retry the workflow to finish the collection."
    report["finished_at"] = utcnow()
    logging_failed = False
    for kind, run_id in log_ids.items():
        body = {"status": report["status"], "finished_at": report["finished_at"], "error_code": report.get("error_code"),
                "snapshot_id": report.get("datasets", {}).get(kind, {}).get("snapshot_id")}
        try:
            status, _ = db.api("PATCH", "fantasy_refresh_runs?id=eq." + run_id, body)
            logging_failed |= status != 204
        except Exception:
            logging_failed = True
    if logging_failed:
        report.update(status="failed", error_code="REFRESH_LOG_FINISH_FAILED")
    path = db.ROOT / "reports" / "refresh-latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = ["## Basketball data refresh", "", "Result: **" + report["status"] + "**", "", "Season: 2026–27. Current injury ingestion is excluded.", ""]
    for kind, result in report.get("datasets", {}).items():
        summary.append(f"- {kind}: {result['records']} records; {'updated' if result['changed'] else 'unchanged'}.")
    if report.get("error_code"):
        summary.append("Error code: `" + report["error_code"] + "`. The last successfully published snapshots remain available.")
    summary.append("\nSuccessful retrieval does not establish the underlying statistics' observation time.\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write("\n".join(summary))
    print("Refresh " + report["status"] + "; attempts=" + str(report["attempts"]) + "; report=reports/refresh-latest.json", flush=True)
    return report


if __name__ == "__main__":
    raise SystemExit(0 if run()["status"] == "succeeded" else 1)
