# Fantasy Basketball Trade & Roster Analyzer — Project Plan

## 1. Purpose and current scope

Build a fully responsive website for an ESPN fantasy basketball manager to answer two questions:

1. Is this trade reasonably balanced when comparing the players being exchanged?
2. How does accepting it change my own team's combined statistics, strengths, weaknesses, and availability?

The manager manually enters their roster and selects players to give and receive. The other manager's full roster is not required. The product must clearly distinguish overall trade value from benefit to the user's particular team.

This document is the only deliverable for the planning stage. No application setup, implementation, dependency installation, or deployment is authorized in this stage.

## 2. Confirmed requirements

| Area | Requirement |
| --- | --- |
| League | ESPN fantasy basketball; 10 teams; 13 players per roster |
| Scoring | Eight categories (8CAT), excluding turnovers |
| Entry | Manual player selection; no ESPN login or automatic league import |
| Analysis | Standalone trade evaluation and impact on the analyzing manager's roster |
| Results | Category gains/losses, combined team statistics, injury concerns, upcoming schedules |
| Additional features | Player comparisons and counteroffer suggestions |
| Design | Simple, modern, accessible, and easy to understand |
| Devices | Phones, tablets, laptops, and desktops |
| Hosting and storage | Vercel for the website; Supabase for shared basketball data and scheduled refreshes |

### Working assumptions

- Use the conventional eight categories below. Confirm their exact match against the friend's ESPN settings during initial review; do not substitute a points-league formula.
- Assume a redraft league for initial player evaluation: current-season production matters, with no keeper contracts or future draft picks.
- Use Supabase for shared basketball data, targeting free-tier usage subject to verified limits. No user accounts or paid AI service in the initial version; save personal rosters and scenarios in the current browser. Supabase does not itself supply basketball statistics.
- Whether the league is head-to-head categories or season-long rotisserie remains unconfirmed. Category changes work for either; do not predict standings or match wins.
- Active lineup slots, bench/IR rules, positional limits, and transaction limits remain unconfirmed. A 13-player roster does not mean all 13 players score every day.
- Start with a 13-player capacity. Support incomplete roster drafts, but label their impact analysis as partial. Treat additional IR capacity as a later settings extension if needed.

## 3. Terms and categories in plain language

A roster is the manager's fantasy team. A category is one kind of basketball statistic used to compare teams. An uneven trade exchanges different numbers of players, such as two players for one.

| Category | Meaning | Favorable direction |
| --- | --- | --- |
| PTS | Points scored | Higher |
| REB | Rebounds: recovering the ball after a missed shot | Higher |
| AST | Assists: passes that lead to a made basket | Higher |
| STL | Steals: taking possession from the opposition | Higher |
| BLK | Blocks: blocking an opponent's shot | Higher |
| 3PM | Three-point shots made, not three-point shooting percentage | Higher |
| FG% | Percentage of field-goal attempts made | Higher |
| FT% | Percentage of free-throw attempts made | Higher |

Turnovers must not influence trade scores, recommendations, or category summaries. Expand abbreviations in tooltips and accessible labels.

## 4. Primary user flow

1. Open the analyzer with league defaults visible: 8CAT, 10 teams, 13 players.
2. Build “My roster” with searchable player selection. Show player name, NBA team, and position where verified. Show roster count and let the manager edit or remove selections.
3. Choose “I give” from the saved roster and “I receive” from the player catalog. Support multi-player deals. A trade-only mode allows analysis without entering the full roster.
4. Select the analysis basis: current-season per-game averages by default; recent form only when sufficient data exists. Select a dated upcoming schedule window separately.
5. Analyze the trade. Lead with a short verdict, biggest category gains/losses, and material availability concerns.
6. Inspect separate “Trade value” and “My roster impact” results, then player comparisons, schedule details, and suggested counteroffers.
7. Change players or assumptions and recalculate. Save a scenario locally or reset it.

Trade-only mode must not invent a roster-impact result. Entering a roster later enables that analysis without rebuilding the trade.

## 5. Features for the first complete release

### A. Roster and trade builder

- Search with keyboard navigation and touch-friendly results; distinguish players with similar names using stable IDs and team details.
- Prevent duplicate selections, a player appearing on both trade sides, outgoing players absent from the user's roster, and incoming players already owned.
- Require at least one player on each side. Provide clear inline correction messages.
- Preserve the user's work in browser storage; provide explicit clear/reset controls and handle unavailable storage gracefully.
- Show before/after roster sizes. For trades that exceed 13 players, require explicit drop selections before presenting a completed roster scenario.
- For trades that leave an open slot, show the vacancy and let the manager optionally select a replacement. Keep the trade-only package evaluation separate from drops/additions used to complete the roster.
- Warn that position and lineup legality require actual league rules; do not claim ESPN approval.

### B. Trade evaluation

- Display each package's eight-category contributions and an explained relative value estimate.
- Use transparent statistical calculations rather than an unexplained AI verdict or FantasySP's proprietary ratings.
- Explain trade-offs: for example, a package may add rebounds and blocks while reducing free-throw efficiency.
- Summarize as “leans toward your side,” “roughly balanced,” or “leans toward their side” only when the model and data support that label. Otherwise show the category comparison with an insufficient-data notice.
- Show the statistical basis, sample size, method, and data timestamp. An estimate of value is not a guarantee of future performance or acceptance by the other manager.

### C. Personalized roster impact — central feature

- Construct the actual post-trade roster: existing roster minus outgoing players and explicit drops, plus incoming players and explicit replacements.
- Compare before, after, and change for all eight categories.
- Present combined per-game production, roster size, and category direction. Explain that summing each player's per-game average describes roster production potential; it is not the team's actual daily fantasy score.
- Include average production per rostered player as supporting context when roster sizes differ. Never use it alone to decide whether an uneven trade is beneficial.
- Explain why a higher general-value package may still weaken categories the manager cares about.
- Allow optional emphasis on selected categories, with all eight equally weighted by default. Keep excluded/emphasized categories visible and explain their effect on the recommendation.
- Describe strengths and weaknesses relative to the user's own before/after profile and an explicitly named reference pool. Do not fabricate league rankings without other rosters.

### D. Injury and schedule context

- Show sourced injury designation, update time, and reported return information when available. An unknown status must not appear as healthy.
- Separate confirmed status from uncertainty. Do not invent an injury probability or return date from a status label.
- Show upcoming game counts for outgoing/incoming players and both roster scenarios over the same explicit date range.
- Let the user select an IANA timezone, defaulting to the browser timezone; display it with schedule dates and use it consistently when determining the date range.
- Estimate scheduled production from per-game rates and scheduled games, clearly labeling it as assuming participation and ignoring bench/lineup limits unless configured.
- Show injury concerns beside these estimates. Offer transparent include/exclude scenarios for unavailable players rather than silently applying arbitrary risk multipliers.
- Missing injury or schedule data must produce a visible limitation, not a fabricated conclusion.

### E. Player comparisons

- Compare selected players with consistent stat windows across all eight categories, shooting volume, games played, minutes where available, injury status, and upcoming games.
- Support comparing both trade packages as well as individual players.
- Make gains and losses readable as numbers and text, not only colored charts.

### F. Counteroffer suggestions

- Generate a small, ranked list of alternative packages using the same category and value calculations as the main analyzer; no paid language-model integration is needed.
- Let the manager optionally enter candidate players available from the other manager. Without that list, label suggestions as hypothetical and ownership unverified.
- Use only the user's roster for outgoing candidates. Prefer small changes to the current proposal, respecting roster capacity and explicit drop/replacement choices.
- Explain how each alternative changes category impact, value balance, and availability concerns; let the manager load it into the builder.
- Cap search size for responsive performance and avoid duplicate or invalid offers. If no defensible suggestion exists, say so.
- Do not claim to know what benefits the other roster or what its manager will accept.

## 6. Calculation design and safeguards

### Aggregate statistics correctly

- Store season/window totals and games played, including field goals made/attempted (FGM/FGA) and free throws made/attempted (FTM/FTA).
- Derive each player's counting-stat rate from that same window. Sum player rates for the roster's combined per-game profile.
- Calculate roster FG% as summed FGM rates divided by summed FGA rates; calculate FT% in the same way. Never average player percentages directly.
- In schedule estimates, weight counting stats and shooting makes/attempts by each player's scheduled games before aggregating. Keep this separate from historical combined per-game output.
- Example: two players shooting 5/10 and 1/1 combine to 6/11, or 54.5%, rather than the simple average of 50% and 100%.
- Show shooting changes in percentage points. Handle zero attempts as unavailable, not zero percent. Calculate at full precision and round only the displayed results.
- Always compare the same season and statistical window. Show inadequate samples and missing fields explicitly; do not silently mix windows or treat missing stats as zero.

### Explain relative trade value

- Proposed model: standardize each counting-stat rate against a disclosed pool of eligible NBA players, then combine category contributions with equal default weights.
- For shooting categories, use a volume-aware contribution such as `(player FG% - reference FG%) × FGA per game`, with an equivalent FT calculation, before standardizing. This avoids overrating low-volume shooters.
- Exclude turnovers entirely. Document sample-size eligibility, reference-pool rules, and zero-variance handling before implementing the model.
- Evaluate uneven packages alongside explicit roster completion and replacement costs. Signed standardized values must not be presented as a ratio or a percentage chance of winning.
- Use the 10 × 13 = 130 roster spots only as rough league-depth context for a replacement baseline. It does not identify the league's actual available players.
- Review balance-label thresholds against representative trades with the friend before calling the model validated. Keep category evidence more prominent than the composite score.
- Historical rates and schedule-based estimates are not a rest-of-season forecasting model. Do not label them as future projections without the necessary forecasting work.

## 7. Data feasibility — resolve before committing to a live release

Vercel hosts the website and Supabase stores data; neither supplies basketball statistics. Use multiple sources where useful, with one designated primary source per dataset and explicit fallback rules. The initial read-only feasibility check below verified core statistical coverage, but did not establish a complete, production-ready free-data pipeline.

### Proposed source assignments — candidates, not final selections

| Dataset | First candidate to test | Backup or verification candidate | Main uncertainty |
| --- | --- | --- | --- |
| Players and category statistics, including shooting totals | SportsDataverse downloadable datasets, subject to applicable licensing | Separately permitted provider/import path | Hosted ingestion, source rights, update delay; direct ESPN collection is not the default |
| Upcoming schedules | Validated SportsDataverse schedule snapshot with TBD games separated | BALLDONTLIE free Games endpoint, not yet runtime-tested | Updates to unassigned games, postponements, usage conditions, cloud access |
| Injury designations and report timestamps | SportsDataverse official-report snapshots with explicit freshness limits | Newer official report linked for verification; user-entered scenario overrides | Timely automated ingestion and rights remain unverified; daily archive is not live |

- ESPN fantasy basketball is free to play. Publicly accessible feeds are separate from a supported developer service or a license to redistribute data; do not infer usage permission from technical access alone.
- The analyzer needs NBA statistics plus the supplied league rules. It does not need ESPN's proprietary fantasy rankings, forecasts, or private league access because rosters are entered manually.
- SportsDataverse's ESPN-derived datasets may offer another delivery path, but are not an independent statistical source when derived from ESPN.
- `nba_api` is a community client, not a hosted data provider. Its maintainers warn of cloud-network access problems; do not assume Vercel or Supabase can retrieve its underlying feeds reliably.
- BALLDONTLIE's documented free tier includes players, teams, and games, but not player game statistics or injuries. Use it only for covered needs, subject to testing.
- Official NBA injury reports are authoritative reports, not necessarily a ready-to-use JSON feed. Verify parsing feasibility before planning an automated fallback. Missing a player from a report must not automatically mean healthy.

### Data-feasibility procedure

The first local/read-only pass is recorded below. Follow this procedure to close remaining gaps before a live release. Do not create the full app or provision services as part of this check without authorization for those actions.

1. **Verify access and usage conditions:** inspect candidate documentation, required authentication, permitted use, rate limits, refresh constraints, and any recurring cost. Mark unclear terms as unresolved rather than assuming permission.
2. **Retrieve representative records:** check current-season player identifiers, games played, PTS, REB, AST, STL, BLK, 3PM, FGM/FGA, and FTM/FTA. Verify raw totals or enough consistent data to derive them, including rounding precision. Recent-form windows require game-level data or an equivalent verified source.
3. **Verify schedules and injuries:** check future games, timestamps/timezones, postponement handling, injury statuses, and actual report freshness. Test missing, stale, and conflicting records as well as successful responses.
4. **Verify the reference pool:** confirm the source can supply enough eligible players for trade-value normalization, not just the 13-player sample roster. Validate pagination, full-pool request volume, and stable player/team mapping.
5. **Test deployment access:** test the intended Supabase refresh runtime and Vercel read path in a minimal hosted probe when service access is authorized and available. A successful local/browser request is not a hosted-access pass. Otherwise mark this check pending.
6. **Check analytical usefulness:** use a representative 13-player roster and a sample trade; independently verify category changes and volume-weighted shooting percentages from retrieved data.
7. **Estimate operating limits:** measure requests per refresh, dataset/storage size, and expected compute usage against current provider and Supabase limits. Choose refresh intervals based on these measurements.
8. **Record the decision:** add a coverage matrix with each requirement marked verified, partial, failed, or untested; name the chosen sources, timestamps, known gaps, fallback behavior, and any cost. Proceed with a live-data design only when core statistical coverage is verified; keep remaining hosted/injury/schedule checks explicit release dependencies.

If free sources leave a gap, investigate a different source or a transparent manual/import workflow before considering paid access. Do not purchase subscriptions. A clearly labeled demo can validate interaction and calculations, but does not fulfill live injury/schedule requirements.

### Combining sources and refreshing Supabase

- Give each player and team an internal ID and maintain verified source-ID mappings. Do not merge records on name alone; account for player team changes.
- Store source, season/window, source update time where available, retrieval time, and completeness for each dataset. Keep retrieval time distinct from the time the underlying information was updated.
- Normalize category names, units, season identifiers, and UTC game timestamps. Do not combine inconsistent statistical windows or overwrite complete records with partial responses.
- Resolve injury conflicts using source authority, report scope, and update time; preserve provenance and show unresolved uncertainty. Do not silently switch individual statistical fields between providers.
- Proposed refresh targets: player statistics once daily after completed games are available; schedules daily with additional checks where postponements matter; injuries every 30–60 minutes during relevant game periods. These are starting targets, subject to verified limits, source update cadence, and quota estimates.
- Use scheduled refresh jobs rather than calling all providers on every page view. Validate a refresh before promoting it to the current dataset; keep the last valid snapshot when a source fails.
- Make stale-data thresholds explicit per dataset. Display last-updated times and limitations; missing injury data remains unknown and unavailable schedules disable schedule estimates.
- Maintain provider-independent data structures. Keep credentials server-side. Do not scrape FantasySP or reuse its proprietary ratings.

## 8. UI/UX and responsive design

- A focused analyzer workspace with a compact header, restrained neutral palette, one accent color, clear type hierarchy, and generous spacing. No decorative basketball imagery is necessary.
- Desktop: roster and trade panels alongside a wider results area. Keep the before/after comparison easy to scan.
- Tablet: adapt panels to two columns where space allows, with results below.
- Phone: stack roster, trade builder, and results; use expandable sections and a reachable analysis action. Keep selections and errors visible above any sticky controls.
- Use readable category cards on narrow screens; allow contained horizontal scrolling only for detailed comparison tables, with clear row labels.
- Provide a short explanation at first use and contextual glossary tooltips. Default to the key findings, with detailed methodology expandable.
- Design loading, empty, partial-roster, stale-data, no-results, invalid-trade, and provider-error states.
- Target WCAG 2.2 AA: keyboard operation, visible focus, semantic labels, screen-reader result announcements, sufficient contrast, reduced-motion support, and touch targets around 44px.
- Verify at widths around 320, 375, 768, 1024, and 1440px, landscape orientations, and 200% zoom. No page-wide horizontal overflow.

## 9. Proposed technical approach

- Next.js with TypeScript, hosted on Vercel. Choose current supported versions when implementation begins.
- Use a lightweight responsive styling system, such as Tailwind CSS, and accessible primitives for complex selection controls. Avoid unnecessary UI dependencies.
- Keep calculations in pure, typed modules shared by the roster comparison, trade evaluation, and counteroffer engine.
- Use local browser persistence for roster/settings/scenarios; no cross-device synchronization is implied.
- Proposed data flow: basketball sources → scheduled Supabase Edge Function → validated Supabase database snapshots → Vercel-hosted read routes → browser trade calculations.
- Use Supabase Cron to invoke authenticated refresh functions. Keep provider credentials and Supabase secret/service credentials in server-side secret storage; never expose them in the browser.
- Use Supabase Postgres for normalized player/team records, provider-ID mappings, statistical windows, schedule entries, injury records, dataset versions, and refresh-run status. Keep the previous successful dataset available during failed or incomplete refreshes.
- Serve only public analysis fields through read-only routes. Restrict ingestion writes to trusted backend functions, configure least-privilege access and row-level security for any exposed tables, and validate query inputs. User accounts are not required for the initial data pipeline.
- Recalculate interactive trades locally from normalized data when practical. Cache reads by dataset version so an analysis uses one consistent snapshot, with separate freshness indicators for stats, schedules, and injuries.
- Do not rely on a function's memory or filesystem as durable storage. Avoid additional databases, caches, or paid services unless measured needs justify them. Verify current Supabase free-tier capacity and operational restrictions; do not promise permanent zero-cost availability.
- Represent players, stat windows, schedules, injury records, league settings, rosters, trade scenarios, and analysis results with stable schemas.
- Data states must distinguish live/current, cached/stale, user-imported, and demo data. Never silently switch a live analysis to sample numbers.

## 10. Delivery sequence after planning

1. **Complete data feasibility (in progress):** the local sample calculation, schedule placeholder handling, and canonical injury-ID matching have been checked below. Next establish the permitted production source path, timely injury ingestion, and hosted access/runtime limits. Output: final source assignments and explicit release limitations. No full application build in this step.
2. **Build the data pipeline and responsive core:** once implementation is authorized, configure Supabase schema/access policies and refresh jobs for verified sources, then build roster/trade selection, validation, accessible layouts, and local scenario persistence. Use clearly labeled sample data only where needed during development. Output: a verified shared-data read path and complete input flow on phone and desktop.
3. **Implement analysis:** package comparison, roster changes, weighted percentages, uneven-trade handling, and concise explanations. Output: independently checked category results.
4. **Integrate context and extras:** real data if feasible, injury/schedule views, player comparison, and bounded counteroffers. Output: all requested features with visible data limitations.
5. **Verify and prepare Vercel deployment:** targeted tests, responsive/accessibility checks, production build, and deployment instructions. Publish only during an authorized implementation/deployment stage.

Each step should leave a usable, reviewable result. Resolve live-data feasibility early rather than treating it as final polish.

## 11. Verification and acceptance criteria

- A manager can manually enter a 13-player roster and analyze a trade without entering the other roster.
- Trade-only analysis works independently; personalized results require roster input and disclose partial rosters.
- All eight categories show before/after values and changes; turnovers never influence results.
- Verify weighted shooting percentages, zero attempts, missing values, sample sizes, and consistent windows against hand-calculated examples.
- Verify one-for-one, two-for-one, one-for-two, duplicate-player, required-drop, and open-slot scenarios. A trade followed by its exact reversal restores the original roster statistics.
- Verify schedules across timezone/date boundaries, injured players, and stale/missing data. No unsupported medical or lineup certainty appears in the result.
- Counteroffers satisfy player-selection and capacity rules, use the same calculation engine, and disclose unverified opponent ownership.
- Use focused unit tests for analytical rules and a small set of end-to-end tests for roster entry, analysis, editing, persistence, and error recovery.
- Check touch, keyboard, screen-reader labels, zoom, narrow screens, and supported desktop/mobile browsers. Production build must pass before deployment.
- A real-data release requires verified data access and functional injury/schedule coverage. If these remain unavailable, identify the release as a demo and list the outstanding requirement.
- Verify source-ID mapping, conflicting reports, refresh failures, partial responses, consistent dataset promotion, stale-data indicators, and recovery using the last valid snapshot. Verify that visitors cannot write shared data or access backend credentials.
- Have the friend review representative results for usefulness and understandable explanations; agreement with a familiar website's proprietary score is not a correctness test.

## 12. Deferred scope

ESPN authentication/import, automatic roster updates, other-manager roster analysis, win probabilities, full lineup optimization, league standings simulation, keeper/dynasty valuation, accounts, cloud synchronization, notifications, and paid AI commentary are outside the first release. Shareable scenarios and automated trade discovery can follow once the core is useful and data access is stable.

## 13. References and research notes

- [FantasySP trade analyzer](https://www.fantasysp.com/nba_trade_analyzer): reference for package entry and general trade analysis; use an original interface and transparent model.
- [ESPN scoring settings](https://support.espn.com/hc/en-us/articles/360000069512-Scoring-Settings): league settings can vary, so retain the explicit 8CAT configuration supplied by the friend.
- [NBA box-score explanation](https://jr.nba.com/how-to-read-a-box-score): category terminology and stat abbreviations.
- [BALLDONTLIE NBA documentation](https://docs.balldontlie.io/): candidate provider only; its documented tiers distinguish player-directory access from statistics and season-average access. Verify all required endpoints and terms before choosing it.
- [Vercel environment variables](https://vercel.com/docs/environment-variables): deployment configuration for any server-side provider credentials.
- [hoopR ESPN endpoint documentation](https://hoopr.sportsdataverse.org/articles/espn-endpoints.html): community-maintained documentation for public NBA feeds; coverage must be verified against actual responses.
- [SportsDataverse basketball tools and datasets](https://hoopr.sportsdataverse.org/): candidate statistical datasets and cross-source mappings; verify licensing and freshness for selected datasets.
- [`nba_api` project](https://github.com/swar/nba_api): candidate NBA.com client and documented cloud-access limitations.
- [Official NBA injury reports](https://official.nba.com/nba-injury-report-2026-27-season): candidate injury verification source; evaluate parsing and update handling.
- [Supabase Cron](https://supabase.com/docs/guides/cron) and [scheduled Edge Functions](https://supabase.com/docs/guides/functions/schedule-functions): proposed scheduled ingestion mechanism.

Research and the initial read-only data checks were performed on November 10, 2026, Asia/Manila. Hosted Vercel/Supabase access remains untested. Dataset ending-year key `2027` refers to the 2026–27 season.

## 14. Initial feasibility findings — November 10, 2026

### Decision

**Free data is technically sufficient for a statistical prototype, but the full live-data release is not yet cleared.** Current-season downloads support all eight categories, exact shooting totals, a meaningful reference pool, player comparisons, and sample roster analysis. Remaining concerns are production-use conditions, current injury coverage, cross-source matching, schedule validation, and access from the intended hosted runtime.

Only `plan.md` was changed. Probes ran in memory using read-only network requests; no application files, accounts, subscriptions, or hosted services were created. The local network sandbox initially rejected requests; the approved outside-sandbox checks below succeeded. These results do not demonstrate access from Supabase or Vercel.

### Coverage matrix

| Requirement | Result | Evidence and limitation |
| --- | --- | --- |
| Player directory | Verified in downloaded snapshot | 522 unique player IDs across 30 roster teams in `rosters_2027.csv` |
| All eight categories and shooting volume | Verified in downloaded snapshot | Season-stat CSV: 19,638 long-format rows for 461 players; includes games played, counting totals, FGM/FGA, FTM/FTA, and 3PM/3PA |
| Reference pool | Verified for a provisional rule | 360 players had at least five games and all required fields; all 360 mapped to the roster snapshot; no duplicate player/category/stat keys found. Five games is a probe filter, not the final eligibility policy |
| Recent-form inputs | Partial | 4,145 player box-score rows include dates, season type, counting stats, shooting attempts, and DNP flags. Rolling-window calculations and complete league-wide reconciliation remain untested |
| Schedules | Partial | 1,206 unique game rows with UTC timestamps and scheduled/final states, including future dates. All rows say regular season, but there are 32 distinct team IDs versus 30 roster teams; investigate unexpected IDs and schedule completeness before calculating reliable totals |
| Injury records | Partial | ESPN returned structured statuses and per-entry dates. SportsDataverse's official-report-derived CSV had 37,843 historical listing rows, but its latest underlying report was November 9 at 00:00 US Eastern; too old for a 30–60-minute update promise |
| Cross-source injury matching | Partial | Current crosswalk has 482 rows and 472 usable NBA-to-ESPN mappings. Only 42 of 63 named entries in the latest injury report mapped automatically; 21 remain unresolved |
| Sample roster arithmetic | Verified for the sample | A 13-player test roster, one-for-one trade, all category changes, and weighted percentages were recomputed; exact-fraction delta arithmetic matched full-roster recomputation |
| Season/box-score agreement | Verified for two sampled players | Luka Doncic and Giannis Antetokounmpo each had 10 played games; their raw category and shooting totals matched independently summed regular-season box scores |
| Source permission for production | Unresolved; ESPN restriction identified | Disney's published terms restrict automated extraction. Public access is not sufficient approval for the proposed ESPN refresh/database pipeline. See usage findings below |
| Provider costs | Partial | Tested ESPN and GitHub responses required no API key or payment; no supported service or unlimited-use guarantee was established |
| Hosted access and recovery behavior | Untested | No Supabase/Vercel project was connected. Scheduled refreshes, permissions, transactional snapshot promotion, stale/conflict handling, and recovery require implementation-stage checks |

### Reproducible sources and observations

ESPN endpoints that returned HTTP 200 without authentication from the approved local probe:

- [Teams](https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams?limit=100)
- [Lakers roster](https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/13/roster)
- [Lakers schedule for ending year 2027](https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/13/schedule?season=2027): 80 listed events, including future games. Do not infer a complete season from this count.
- [Doncic season statistics](https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/3945274/stats?season=2027): separate averages and integer totals, including shooting made/attempted pairs. The response contains historical season rows too; explicitly select ending year 2027 and aggregate team stints without double-counting.
- [League injuries](https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries): approximately 1.06 MB with 29 team groups in the sampled response. The first sampled athlete object lacked a direct `id`, while its profile link contained an ID. Do not join on names alone or treat absent groups as healthy. One record also had structured `Out` status and a separate fantasy `GTD` designation; choose and document status semantics instead of treating those fields as interchangeable.

A speculative bulk endpoint at `site.web.api.espn.com/apis/fittwo/v3/sports/basketball/nba/athletes` returned HTTP 404 with the tested parameters. This rules out that tested route, not every possible bulk route.

SportsDataverse downloads that were successfully parsed:

| Asset | Bytes downloaded | Asset update time (UTC) |
| --- | ---: | --- |
| [Season statistics CSV](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_nba_player_season_stats/player_season_stats_2027.csv) | 3,951,962 | November 10, 12:57 |
| [Schedules CSV](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_nba_schedules/nba_schedule_2027.csv) | 2,924,972 | November 10, 12:55 |
| [Rosters CSV](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_nba_rosters/rosters_2027.csv) | 224,787 | November 10, 12:56 |
| [Player box scores CSV](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_nba_player_boxscores/player_box_2027.csv) | 2,109,783 | November 10, 12:55 |
| [Official-report-derived injuries CSV](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_stats_injury_report/injury_report_2027.csv) | 6,709,232 | November 9, 18:02 |

The [2027 player crosswalk](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_crosswalk/nba_player_crosswalk_2027.csv) was also parsed. Preserve match method/confidence, detect ambiguous mappings, and review unresolved current players rather than silently dropping them.

Asset upload time does not establish the age of the observations inside it. Injury `report_datetime` is a naive US Eastern timestamp; interpret using `America/New_York`, including daylight-saving transitions. The latest tested snapshot contained 79 listings: 63 named entries and 16 entries without a player/status. These can represent a team report not yet submitted and must not become healthy-player records. Availability reasons can also include G League assignments, not just injuries.

### Sample calculation from retrieved data

This is a deterministic synthetic test roster, not the friend's actual team or a recommendation. Roster: Luka Doncic, AJ Dybantsa, AJ Green, Aaron Gordon, Aaron Nesmith, Aaron Wiggins, Ace Bailey, Aday Mara, Adem Bona, Ajay Mitchell, Al Horford, Alex Caruso, and Alex Karaban. Replace Doncic with Giannis Antetokounmpo, leaving the other 12 players unchanged.

| Combined per-game profile | Before | After | Change |
| --- | ---: | ---: | ---: |
| PTS | 156.4952 | 144.6952 | -11.8 |
| REB | 56.4959 | 61.4959 | +5.0 |
| AST | 30.3105 | 27.7105 | -2.6 |
| STL | 10.1849 | 9.1849 | -1.0 |
| BLK | 7.7672 | 8.0672 | +0.3 |
| 3PM | 19.7210 | 14.7210 | -5.0 |
| FG% | 46.5081% | 47.4851% | +0.9770 percentage points |
| FT% | 80.3926% | 72.2494% | -8.1433 percentage points |

Rates were derived from integer totals divided by each player's games played, then combined. Shooting percentages were calculated from combined made/attempted rates. Direct roster recomputation and before-minus-outgoing-plus-incoming arithmetic agreed using exact fractions. These numbers test the aggregation method; they are not actual fantasy lineup totals, a trade fairness score, or a validated forecast.

### Usage and cost findings

- [Disney's terms, Section 2.B](https://disneytermsofuse.com/english/) include ESPN-branded products and restrict automated access/extraction and database compilation. This is an identified production-use constraint, not a conclusion that paying ESPN would solve access. Do not select direct ESPN ingestion without establishing applicable permission. No further ESPN collection pipeline was built.
- The producing [hoopR NBA data repository](https://github.com/sportsdataverse/hoopR-nba-data/blob/main/LICENSE.md) and [NBA Stats data repository](https://github.com/sportsdataverse/hoopR-nba-stats-data/blob/main/LICENSE.md) declare CC BY 4.0. Preserve attribution and transformation notes. The shared release repository has a separate [MIT license](https://github.com/sportsdataverse/sportsdataverse-data/blob/master/LICENSE). Confirm the terms applicable to the exact release assets and upstream rights before public use; do not assume a software license resolves all data rights.
- [BALLDONTLIE's documented free tier](https://docs.balldontlie.io/) covers players, teams, and games, with a documented five requests/minute limit; player statistics and injuries are excluded. It remains a potential schedule fallback, not a verified runtime fallback: no account/key was created or tested.
- [TheSportsDB](https://www.thesportsdb.com/docs/api) offers a free API, but full current NBA statistical/injury coverage was not tested in this pass. Its [usage terms](https://api.thesportsdb.com/docs_terms_of_use.php) also distinguish API content and third-party rights. Keep it a candidate, not an established solution.
- [Supabase's current free plan](https://supabase.com/pricing) lists 500 MB database capacity, 5 GB egress, and 500,000 Edge Function invocations, with inactivity-related pausing. These are platform limits, not data-provider quotas. They do not establish suitability for an unknown traffic level.
- Four core CSV files total approximately 9.21 MB for one full pull. Adding the tested injury CSV brings it to approximately 15.92 MB, excluding the crosswalk and HTTP overhead. Retain normalized current/previous snapshots rather than appending full raw archives forever.
- A daily four-file core pull plus an hourly-to-half-hourly injury pull would be roughly 28–52 asset downloads/day, excluding metadata, crosswalks, and retries. Polling a daily injury archive more frequently cannot make its underlying data current. Prefer release-change checks and fetch only changed assets.
- Download volume into a refresh function is not the same as Supabase database egress to visitors. Actual database size, indexing, client payloads, runtime memory/CPU, and traffic costs remain unmeasured. These season files grow over time; split refresh work into bounded jobs and measure before selecting the deployment schedule.

### Revised recommendation and next work

This initial recommendation is refined by the tested resolutions in Section 15 below; the Section 14 observations remain a record of the first snapshot check.

1. Use the tested downloadable statistical datasets as the leading prototype candidate, conditional on applicable data-use rights. They avoid hundreds of per-player requests and already contain a useful player pool. Keep ESPN listed as technically tested, not approved for production ingestion.
2. Resolve injury freshness and the 21 unmatched latest-report entries. Evaluate a current, permitted official-report ingestion path or another provider; a daily archive is only a historical/stale fallback. If no free option meets the requirement, disclose that result before changing cost or scope.
3. Investigate the two unexpected schedule team IDs and incomplete-season/placeholder behavior. Validate against the 30-team roster directory; do not silently count or discard questionable games.
4. After the data-use and coverage decisions, test a minimal Supabase refresh and Vercel read path when project access is available. Verify snapshot consistency, public read restrictions, secrets, stale-data behavior, and measured quotas before the application build.
5. Update the source assignments and pipeline design from those results. The next step is to close these concrete data gaps; the full live website is not yet ready to be built against an assumed complete free feed.

## 15. Gap-resolution checks and selected handling

Follow-up read-only checks on November 10, 2026. The transformations below were executed in memory; they are verified analytical rules for the later implementation, not a deployed importer or application. Only this plan is persisted.

### A. Schedule IDs — identified and handled in the probe

The unexpected team IDs are `-1` and `-2`, both explicitly named `TBD`. They occur together in six placeholder games, not as two extra NBA franchises:

| Game ID | Date/time in source (UTC) |
| --- | --- |
| 401909450 | December 4, 2026, 05:00 |
| 401909451 | December 4, 2026, 05:00 |
| 401909452 | December 5, 2026, 05:00 |
| 401909453 | December 5, 2026, 05:00 |
| 401909454 | December 8, 2026, 05:00 |
| 401909456 | December 11, 2026, 05:00 |

**Verified result:** requiring two distinct, recognized NBA team IDs retained 1,200 unique assigned games. Every one of the 30 teams has 80 assigned games in this snapshot. This explains the anomaly; it does not prove the final schedule is complete. Do not infer or fabricate the missing assignments or treat placeholder times as confirmed tip-offs.

Implementation rule: retain the six records separately as unassigned; exclude them from player/team game counts. Show “Schedule provisional: some games are not assigned yet” for affected date windows. Reprocess them by stable game ID on later refreshes; count only after valid participants and confirmed date/time arrive. If the source replaces placeholder IDs, deduplicate confirmed events without inventing a correspondence. Continue to handle postponements, cancellations, and unknown dates explicitly.

### B. Injury identity matching — all 63 named entries resolved in the tested report

**Verified result:** all 63 named entries in the tested November 9 report can be assigned to a canonical NBA player ID. The earlier 21 unmatched entries were caused by relying on the current ESPN crosswalk alone.

Checks performed:

1. Merged unambiguous stable NBA/ESPN ID pairs from the [2027](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_crosswalk/nba_player_crosswalk_2027.csv), [2026](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_crosswalk/nba_player_crosswalk_2026.csv), and [2025](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_crosswalk/nba_player_crosswalk_2025.csv) crosswalks. This recovered 13 of the initial 21 entries, without conflicting NBA-ID-to-ESPN-ID pairs in those snapshots.
2. Compared the remaining records to both current roster directories, using normalized full names plus the verified [NBA/ESPN team crosswalk](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_crosswalk/nba_team_crosswalk_2027.csv). Seven more matched uniquely. Normalization handled comma ordering, accents, punctuation, and suffixes; it did not use fuzzy similarity or name alone.
3. Added the [NBA roster dataset](https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_stats_rosters/rosters_2027.csv) to the player directory. It contains 524 unique NBA player IDs. The remaining player, Khalifa Diop (`1631215`), exists there but is absent from the ESPN roster snapshot. Keep his NBA identity; do not manufacture an ESPN ID or statistical history.
4. The injury report's missing ID for Ernest Udeh Jr. was recovered as NBA `1643640`, using a unique normalized-name match within the same verified team in the NBA roster; ESPN alias `5106261` matched the current team too. Record this inferred association's method and evidence.

The union-directory check linked 519 of 522 ESPN roster entries to NBA IDs: 503 through stable crosswalks and 16 through unique normalized-name-plus-team matches. There were no two ESPN IDs mapped to the same NBA ID in the accepted result. Three ESPN entries remain unmatched: Blake Wesley (`4683935`), AK Okereke (`5114350`), and Carson Cooper (`5105817`). They were not among the 63 tested injury entries.

Implementation rule: use an internal player key, with NBA and ESPN IDs as separate aliases. NBA-only and ESPN-only players remain visible; do not discard them. ESPN-only players can retain a provider-specific identity until a verified merge exists. Mark injury coverage unknown where identity cannot be established; missing stats must not become zero production. Stable IDs survive transfers, while current team metadata must be updated separately. Persist mapping evidence, reject collisions, and revalidate newly discovered players every refresh. Success on one report does not guarantee every future record will match.

### C. Injury freshness — newer source verified; automated refresh not yet solved

The [official November 10, 2026, 07:00 US Eastern report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-10_07_00AM.pdf) was opened and its four-page text was readable. Its report time is November 10 at 20:00 Asia/Manila, 31 hours newer than the downloaded archive's latest report. This verifies that newer injury information exists; repeated polling of the old archive is not the solution.

Selected handling for the free prototype:

- Import the latest available archive snapshot with its underlying report time, game date, and coverage. Label it as a reported snapshot, not live injury monitoring.
- Show a direct link to the official report index for current verification. A manager may explicitly override a player's availability for a scenario, with the chosen assumption clearly separate from sourced status. Overrides are user assumptions and do not update shared provider records.
- A later maintenance workflow may accept a reviewed report import containing source URL, original report timestamp, game date, team, player ID, status, and review timestamp. This is a proposed implementation task, not a background process already installed.
- Evaluate automated ingestion of the current official reports only after applicable usage conditions and a production parser are established. The successful web text extraction is not proof of a deployed PDF parser. No PDF dependencies were installed in this planning stage.
- Preserve game-specific scope: a team's “NOT YET SUBMITTED” entry remains unknown. An older game designation must not become an indefinite current status; report absence alone is not a healthy designation.
- If a report fails freshness or coverage checks, keep its historical context but disable any claim of current availability-adjusted estimates. Per-game statistical trade analysis remains usable. Freshness must use the original report timestamp, not its download time.

**Remaining limitation:** reliable automatic 30–60-minute injury updates have not been achieved. The free prototype can expose timestamped snapshots and explicit scenarios; that does not fully satisfy a future promise of automatic current injury coverage. Keep this release limitation visible rather than quietly redefining it as solved.

### D. Source usage — avoid relying on direct ESPN collection

Select downloadable SportsDataverse data as the leading prototype path and retain direct ESPN requests only as historical technical evidence. The producing [NBA data](https://github.com/sportsdataverse/hoopR-nba-data/blob/main/LICENSE.md) and [NBA Stats data](https://github.com/sportsdataverse/hoopR-nba-stats-data/blob/main/LICENSE.md) repositories explicitly declare their data, code, and documentation CC BY 4.0. Document which producer and license apply to each selected release asset.

Add a visible data-credit area identifying the dataset, authors, source release, license link, retrieved version, and transformations (normalization, filtering, ID mapping, and aggregation). The [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/) require attribution and identifying changes. Keep logos, headshots, and provider commentary out of the initial dataset unless their rights are separately verified.

This establishes a concrete declared-license path to evaluate; it does not independently settle upstream ownership or grant permission to collect directly from ESPN. No provider contact, data license purchase, or unsupported claim of production permission was made. If the precise asset rights remain unclear, retain that uncertainty before publishing the data-backed site.

### E. Hosted access — still requires project access

No Supabase or Vercel project credentials/connections are present in the workspace. A local request cannot establish hosted reliability. Do not provision accounts or invent a hosted test result.

The next minimal integration should read one selected release, normalize it into a staging dataset, validate the schedule and identity rules above, and promote it atomically. Vercel should read only the validated public analysis fields. Verify authenticated ingestion, blocked public writes, credential isolation, stale snapshot fallback, quota usage, and rollback. Load-test the full season files as they grow; do not use one long-running function for all datasets by default.

### Current outcome

- **Checked successfully:** schedule placeholder classification and filtering; canonical identities for all 63 named entries in the sampled injury archive; combined-directory matching rules; a newer official injury report is accessible.
- **Concrete plan selected:** downloadable datasets with provenance/attribution, provisional schedule counts, canonical player IDs, timestamped injury snapshots, and explicit availability scenarios.
- **Still unverified:** timely automated injury ingestion, precise release-asset/upstream rights for public use, and Supabase/Vercel execution. No paid service is necessary for the completed checks, but a fully automated free production feed is not yet established.

## 16. Database proof-of-concept setup prepared

Localhost development is the current target; Vercel setup is deferred. Supabase plugin access is not required for the initial path. `.env.local` contains project connection settings and must remain untracked; `.gitignore` now excludes environment files.

- Setup file: `supabase/setup.sql`. Run the whole file in the hosted project's SQL Editor as the project owner. API data keys do not by themselves provide a general SQL/schema-management endpoint.
- Creates three prefixed tables: versioned datasets, current dataset pointers, and private refresh-run logs. It includes row-level security and explicit grants, plus a backend-only function for validating and atomically publishing a staged snapshot.
- Public and signed-in visitors can read only current published basketball datasets. They cannot write data, publish staging records, or read operational logs. The service-role backend performs imports.
- The SQL is rerunnable for this initial version without deleting rows. It does not install scheduled jobs, populate sample/live data, or alter unrelated tables. Future schema changes should use explicit migrations.
- Verified with 19 passing checks in an isolated PGlite PostgreSQL engine: initial application/rerun, anonymous and signed-in access boundaries, staging visibility, publication permissions, snapshot replacement, invalid/missing statistics, duplicate IDs, stale-source rejection, demo/live separation, placeholder-game rejection, injury validation, last-valid-snapshot retention, and RLS on all three tables.
- These are real SQL-engine checks, not tests of the hosted Supabase gateway or concurrency/load behavior. Complete hosted validation after the setup is run. Source and identity validation in the importer remain necessary beyond the SQL's structural checks.
- The user executed `supabase/setup.sql` and confirmed all three tables report `row_security_enabled = true`. The hosted and localhost checks below now verify the read/import/publication path. No extra confirmation is needed for the already requested checks.

## 17. Hosted Supabase and localhost checks completed

On November 10, 2026, `scripts/check_supabase.py` completed **50 passing checks** against the actual hosted Supabase project. The Python standard-library runner uses `.env.local` without logging credentials. The earlier public database-access problem is resolved: publishable-key reads of the public data tables now return HTTP 200, while public reads of private refresh logs are denied.

- Imported a 14-player subset from the verified SportsDataverse season-stat CSV, explicitly marked `data_mode = imported`, with provenance, transformation notes, incomplete-league coverage, and freshness warnings. No full live-data refresh is implied. The source file had 360 players meeting the probe's five-game eligibility rule and was 3,951,962 bytes when fetched.
- Published the sample through the actual database RPC and verified its public readback. All category and shooting-total values survived the round-trip unchanged.
- Verified the same 13-player roster and one-for-one Doncic/Antetokounmpo trade against source totals, including all six counting categories and volume-weighted FG%/FT% before and after the trade. Turnovers are not involved.
- Verified that public clients cannot insert, modify, or delete snapshots, change current-version pointers, publish snapshots, insert refresh logs, or read operational logs. Requests without an API key are rejected. A real signed-in user session was not exercised.
- Invalid shooting totals, duplicate player IDs, and older retrievals were rejected by the hosted publication function. Each failure left the last valid current dataset usable. Unpublished and superseded snapshots were invisible through the public key.
- Kept two valid sample snapshots from the run and one sanitized test-failure log. Deleted only the three deliberately invalid staging snapshots created by the run. No unrelated data was replaced. Retention across repeated runs is not automated yet.
- Stored the auditable results in `reports/supabase-check.json`; the hosted run took approximately 14.44 seconds including the source download and sequential API calls. This is one measured integration run, not a production latency/load benchmark.

`scripts/serve_data_check.py` supplies a read-only localhost diagnostic backend at `127.0.0.1:8765`. A further **nine checks passed**, for **59 hosted/local HTTP checks in total**: database connectivity, sample labeling, eight-category output, agreement with the source calculation, unknown observation-time disclosure, environment-file protection, project-file protection, write rejection, and exclusion of actual API key values from responses.

This is not the finished responsive website. The endpoints are `/api/health` and `/api/sample-trade`; they return JSON and expose no import or administration endpoint. Instructions are in `scripts/README.md`.

**Status update:** the responsive website and expanded catalog described in section 18 now replace this diagnostic-only stage. The earlier proof results remain recorded above. There is no need to reconnect a plugin or redo the successful SQL setup.

## 18. Responsive localhost website implemented

The Next.js application, named **Courtside**, now runs at `http://127.0.0.1:3000` using the existing hosted Supabase project. Vercel setup is deferred. Restart with `npm run dev` if the terminal closes; setup and validation commands are in `README.md`.

### Available workflow

- Start with a labeled example or manually select your own roster, up to 13 players. Partial rosters and trade-only analysis are supported.
- Choose outgoing and incoming players. Uneven trades require explicit drops when the resulting roster exceeds capacity; optional replacement additions are available.
- Analyze the package and the manager's roster before/after across all eight categories. FG% and FT% use attempts as weights. Missing statistics remain unknown instead of becoming zero.
- Switch between per-game profiles and schedule-window production potential, with timezone and 7/14-day controls. Schedule estimates assume participation and do not model daily lineup slots or predict results.
- Emphasize categories, compare up to four players, and explore bounded counteroffers. Package values use a disclosed statistical model and a replacement baseline; they are exploratory, not calibrated trade-market prices or win probabilities.
- Review archived injury context and explicitly exclude selected players from roster/schedule estimates. These assumptions do not silently change historical package values.
- Save scenarios in this browser or export JSON. No sign-in or shared storage of personal rosters is required.
- Use responsive desktop, tablet, and phone layouts, keyboard player search, accessible dialogs, and in-app methodology/data credits.

### Data and credential boundaries

`scripts/import_catalog.py` expanded the proof sample to **530 directory entries, 456 complete statistical records, 1,200 assigned games, and 63 archived injury entries**. Six TBD game placeholders are excluded. Each dataset is validated and published independently; the four kinds are not one atomic release. This is a manually imported snapshot with disclosed provenance, not an automatically refreshed feed.

The server-only data loader reads current published snapshots using the publishable key. The web app does not use the backend secret key. Actual secret-value scanning of rendered HTML and generated client scripts found no exposure, and the environment-file URL returned 404. Environment files remain excluded from version control.

### Verification and remaining work

- Eleven calculation/validation tests cover weighted percentages, missing data, schedule multipliers, uneven trades, ownership/duplicates, trade-only mode, directionality, timezone boundaries, and counteroffer constraints.
- All eight browser tests pass, exercising saved scenarios, manual inputs, uneven trades, counteroffers, explicit availability assumptions, schedule controls, keyboard selection, and layouts at widths 320, 375, 768, 1024, and 1440 pixels.
- Automated WCAG A/AA checks pass for desktop, mobile, roster selection, comparison, help, dataset information, and availability dialogs. Results are recorded in `reports/accessibility.json`. This does not replace manual assistive-technology testing.
- TypeScript checks and the production build pass. Browser screenshots are in `reports/screenshots/`.

The next step is to review the localhost app with a real roster and have the fantasy manager assess whether the explanations and category emphasis match their decisions. Before a public release, finish current injury ingestion, refresh scheduling/retention, exact-source public-use review, and Vercel runtime checks. These limitations are disclosed in the website; no plugin or additional database setup is needed for local review.
