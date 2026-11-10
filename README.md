# Courtside

A responsive ESPN-style fantasy basketball trade and roster analyzer for an
eight-category league without turnovers: 10 teams, 13-player rosters.

## Run locally

Requires Node.js 20.9+ and a hosted Supabase project. The existing project is already
configured through the untracked `.env.local` file. For a fresh setup, copy
`.env.example` to `.env.local`, supply the project settings, and run the entire
`supabase/setup.sql` in the hosted project's SQL Editor.

```powershell
npm install
npm run dev
```

Open **http://127.0.0.1:3000**. Start with the clearly labeled example scenario or
choose **Use my roster**. No Supabase plugin, Docker, local Supabase stack, account
system, or Vercel deployment is needed to use this version.

## What works

The moon/sun button in the top bar switches between light and dark mode. The first
visit follows the device preference; a manual choice is remembered in this browser.

- Search the combined player directory and build a roster of up to 13 players.
- Multi-player trades, trade-only analysis, partial rosters, explicit roster drops,
  and optional replacement additions.
- Before/after comparison across all eight categories; attempt-weighted shooting
  percentages, per-game profiles, and schedule-window production potential.
- Exploratory package values with a disclosed replacement baseline; optional
  category emphasis and bounded counteroffer suggestions with a candidate pool.
- Comparison of up to four players, saved scenarios in browser storage, and JSON
  export of the active analysis view and assumptions.
- Timezone-aware schedule windows and archived availability context, with explicit
  user assumptions for unavailable players. No current injury probability is invented.
- Responsive layouts, keyboard player search, native accessible dialogs, reduced
  motion, local fonts, and semantic category tables.

## Data and refreshes

The app reads only published Supabase snapshots with the publishable key in a
server-only module. Secret/service credentials are not used by the web app or sent
to browsers. User roster/scenario data is saved in the browser, not the shared database.

The local research import currently contains **530 player directory entries, 456
complete statistical records, 1,200 assigned games, and 63 archived injury listings**.
Players with missing statistics remain visible; the analyzer does not invent zeroes.

To refresh the imported datasets manually, from the project root:

```powershell
python scripts/import_catalog.py
```

For the monitored refresh used by automation (players, stats, schedules only):

```powershell
python scripts/refresh_data.py
```

GitHub Actions runs `.github/workflows/refresh-data.yml` daily at **6:17 PM
Asia/Manila** (10:17 UTC), with a manual **Run workflow** option in the repository's
Actions tab. GitHub scheduling is best effort and may run late. The runner reads
three encrypted repository Actions secrets: `NEXT_PUBLIC_SUPABASE_URL`,
`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, and `SUPABASE_SECRET_KEY`. These are separate
from Vercel's environment settings. No credentials are committed, and the backend
secret remains unnecessary for Vercel.

The runner tests its safety checks, retries temporary download/database failures,
validates all three core datasets before publishing, blocks large coverage drops,
and skips snapshots whose content has not changed. Successful runs do not commit
data or trigger a Vercel deployment. The website reads the current Supabase data
through its existing two-minute cache.

Refresh history is recorded in the private `fantasy_refresh_runs` table. Each
workflow run also has a readable summary and a sanitized JSON artifact retained
for 14 days. Inspect **Actions → Refresh basketball data** for failures; GitHub
notification delivery depends on your own notification settings. There is no
custom email/SMS alert or independent missed-run monitor.

The script uses Python's standard library, downloads the selected SportsDataverse
CSV assets, validates source identities/stat totals, and publishes each dataset
atomically. It refuses to overwrite unrelated datasets. Details are saved in
`reports/catalog-import.json`. Each dataset is promoted separately; this is not a
transaction spanning all four datasets. An import failure may require completing
remaining kinds before treating the collection as one release.

The original statistical observation time is unknown; retrieval time is shown
separately and must not be presented as live freshness. The injury data is an
archive and only applies to its report/game dates. Six TBD game placeholders are
excluded from team counts. Current injury ingestion, snapshot/log retention
jobs, season rollover, and a public-release data-rights review remain unfinished. No direct ESPN
scraping pipeline or paid provider subscription is installed.

Credit and links to the producing repositories' declared CC BY 4.0 licenses are
available in the app's **Data & credits** dialog. No third-party player artwork,
proprietary ratings, or provider commentary is used.

## Validation

```powershell
npm run typecheck
npm test
npm run test:e2e
npm run build
python -m unittest discover -s tests -p 'test_refresh.py'
```

Browser tests use installed Microsoft Edge on Windows. On other systems, install
Playwright Chromium with `npx playwright install chromium`; `PLAYWRIGHT_CHANNEL`
can select a different available channel. Tests start/reuse a localhost dev server
and require the configured Supabase data. The test roster is synthetic and is not
the user's actual fantasy roster. Results include automated accessibility checks;
these do not replace complete assistive-technology/user testing.

Earlier 14-player proof scripts are documented in `scripts/README.md`. The older
hosted proof runner intentionally refuses to overwrite the full catalog now in
use, and its diagnostic API's sample-trade route will reject that different data.

`plan.md` contains the requirements, data-feasibility results, database checks, and
remaining release constraints. Hosting on Vercel is deferred until local review.
