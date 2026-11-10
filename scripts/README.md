# Data-pipeline checks

These scripts verify the data connection before the full website is built. They
use Python's standard library and the hosted Supabase schema in `supabase/setup.sql`.
They do not require Docker, the Supabase plugin, Vercel, or npm packages.

Run commands from the project root in PowerShell. Connection settings are loaded
from `.env.local`; keys are not printed or written into reports.

```powershell
python scripts/check_supabase.py
```

This performs hosted read/write/security checks, imports a **14-player sample**
from the current 2026–27 SportsDataverse season-stat CSV, and independently checks
a 13-player roster trade. It is an imported integration fixture, not a complete
live dataset. It does not establish permission for a public data release.

The script keeps its valid sample snapshots and one sanitized refresh log, and
removes its deliberately invalid staging snapshots. On a rerun it refuses to
replace an unrelated current player-stat dataset. Repeated successful runs retain
additional valid proof history; retention should be configured before automation.
If a check fails, it stops and records the failed check; inspect only this proof's
staging IDs in the report before cleanup. No blanket database deletion is used.

Results are saved in `reports/supabase-check.json`. The public-read tests use the
publishable API key without a signed-in user. Actual user-login, Supabase Edge
Function runtime, simultaneous refreshes, and Vercel execution are not tested here.

To inspect the sample through a local HTTP backend:

```powershell
python scripts/serve_data_check.py
```

- Health: http://127.0.0.1:8765/api/health
- Sample trade: http://127.0.0.1:8765/api/sample-trade

This is a read-only diagnostic API, not the website UI. It binds to localhost only,
does not serve project files, and does not return credentials. Press Ctrl+C in its
terminal to stop it. The sample-trade route requires the labeled proof dataset;
it will reject a different current dataset instead of assuming its row order.

The completed hosted run passed 50 checks; a further nine localhost checks were
recorded in the report, including stat reconciliation and credential exclusion.
Running the hosted script again replaces the report; localhost results must be
rechecked for that run before claiming all 59 checks passed again.
