"""Importer protections without network requests or credentials."""
from copy import deepcopy
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import import_catalog as catalog
import refresh_data


def sample():
    directory = [{"player_id": str(i)} for i in range(300)]
    totals = [{"player_id": str(i), "gp": 1, "pts": 10, "reb": 1, "ast": 1, "stl": 1, "blk": 1,
               "three_pm": 0, "fgm": 5, "fga": 10, "ftm": 0, "fta": 0} for i in range(130)]
    games = [{"game_id": str(i), "home_team_id": str(i % 30), "away_team_id": str((i + 1) % 30),
              "starts_at": "2026-11-11T23:00:00Z"} for i in range(1000)]
    return directory, totals, games


class RefreshTests(unittest.TestCase):
    def test_accepts_complete_core(self):
        catalog.validate_core(*sample(), {})

    def test_rejects_invalid_shooting(self):
        directory, totals, games = sample()
        totals[0]["fgm"] = 11
        with self.assertRaisesRegex(RuntimeError, "INVALID_SHOOTING"):
            catalog.validate_core(directory, totals, games, {})

    def test_rejects_unmapped_stats(self):
        directory, totals, games = sample()
        totals[0]["player_id"] = "missing"
        with self.assertRaisesRegex(RuntimeError, "UNMAPPED"):
            catalog.validate_core(directory, totals, games, {})

    def test_rejects_large_coverage_drop(self):
        with self.assertRaisesRegex(RuntimeError, "COVERAGE_DROP"):
            catalog.validate_core(*sample(), {"players": 500})

    def test_rejects_timezone_ambiguity(self):
        directory, totals, games = sample()
        games[0]["starts_at"] = "2026-11-11T23:00:00"
        with self.assertRaisesRegex(RuntimeError, "TIMESTAMP"):
            catalog.validate_core(directory, totals, games, {})

    def test_fingerprint_ignores_record_order_but_detects_changes(self):
        rows = [{"player_id": "a", "pts": 10}, {"player_id": "b", "pts": 20}]
        original = catalog.content_hash(rows, "https://source", {}, [])
        self.assertEqual(original, catalog.content_hash(rows[::-1], "https://source", {}, []))
        changed = deepcopy(rows)
        changed[0]["pts"] = 11
        self.assertNotEqual(original, catalog.content_hash(changed, "https://source", {}, []))

    def test_unchanged_data_skips_writes_and_uses_public_current_view(self):
        rows = [{"player_id": "a"}]
        prior = {"data_mode": "imported", "payload": {"importer": catalog.MARKER, "records": rows, "coverage": {}, "warnings": []}}
        with patch.object(catalog.db, "api", side_effect=[(200, [prior]), (200, [{"snapshot_id": "existing"}])]) as api:
            result = catalog.publish("players", rows, "https://source", {}, [])
        self.assertFalse(result["changed"])
        self.assertTrue(all(call.args[0] == "GET" for call in api.call_args_list))
        self.assertEqual(api.call_args_list[0].kwargs["role"], "public")

    def test_foreign_dataset_is_preserved(self):
        prior = {"data_mode": "live", "payload": {"importer": "unrelated"}}
        with patch.object(catalog.db, "api", return_value=(200, [prior])) as api:
            with self.assertRaisesRegex(RuntimeError, "preserve unrelated"):
                catalog.publish("players", [], "https://source", {}, [])
        self.assertEqual(api.call_count, 1)

    def test_failure_is_sanitized_and_run_logs_are_closed(self):
        def api(method, path, body):
            return (201 if method == "POST" else 204), None
        with tempfile.TemporaryDirectory() as folder, patch.object(refresh_data.db, "ROOT", Path(folder)), \
             patch.object(refresh_data.db, "api", side_effect=api) as calls, \
             patch.object(catalog, "main", side_effect=ValueError("PRIVATE_HEADER_VALUE")):
            report = refresh_data.run()
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["error_code"], "IMPORT_VALIDATION_FAILED")
        self.assertNotIn("PRIVATE_HEADER_VALUE", str(report))
        self.assertEqual(len([c for c in calls.call_args_list if c.args[0] == "PATCH"]), 3)

    def test_transient_failure_retries_and_records_success(self):
        output = {kind: {"snapshot_id": kind, "records": 300, "changed": False} for kind in refresh_data.KINDS}
        output["source_files"] = {}
        with tempfile.TemporaryDirectory() as folder, patch.object(refresh_data.db, "ROOT", Path(folder)), \
             patch.object(refresh_data.db, "api", side_effect=lambda method, *args: (201 if method == "POST" else 204, None)), \
             patch.object(catalog, "main", side_effect=[RuntimeError("SOURCE_DOWNLOAD_FAILED"), output]), \
             patch.object(refresh_data.time, "sleep"):
            report = refresh_data.run()
        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["attempts"], 2)


if __name__ == "__main__":
    unittest.main()
