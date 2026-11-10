-- NBA fantasy analyzer: initial data-pipeline proof of concept.
-- Run this entire file once in your HOSTED Supabase project's SQL Editor.
-- It is safe to rerun this version; it never deletes existing rows.
-- No credentials, sample data, paid extensions, or scheduled jobs are included.
-- This creates only fantasy_* objects in public and does not change other tables.
-- Backend imports use the secret key (service_role); visitors have read-only access.
-- Payload contract: {"records": [...], "coverage": {...}, "warnings": [...] }.
-- Only public basketball information belongs in a payload. No user data or secrets.
-- This SQL checks structure and basic integrity; the importer must also validate
-- source rights, full category coverage, identities, season/window, and freshness.

begin;

create table if not exists public.fantasy_data_snapshots (
  id uuid primary key default gen_random_uuid(),
  dataset_kind text not null check (dataset_kind in
    ('teams', 'players', 'player_stats', 'schedule', 'injuries', 'player_mappings')),
  season integer not null check (season between 1947 and 3000),
  source_url text not null check (source_url ~ '^https://'),
  source_updated_at timestamptz,
  retrieved_at timestamptz not null default now(),
  data_mode text not null default 'live' check (data_mode in ('live', 'demo', 'imported')),
  payload jsonb not null check (
    jsonb_typeof(payload) = 'object'
    and jsonb_typeof(payload -> 'records') is not distinct from 'array'
  ),
  record_count integer generated always as (jsonb_array_length(payload -> 'records')) stored,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  unique (id, dataset_kind, season)
);

create table if not exists public.fantasy_current_datasets (
  dataset_kind text not null,
  season integer not null,
  snapshot_id uuid not null,
  updated_at timestamptz not null default now(),
  primary key (dataset_kind, season),
  foreign key (snapshot_id, dataset_kind, season)
    references public.fantasy_data_snapshots (id, dataset_kind, season)
);

create table if not exists public.fantasy_refresh_runs (
  id uuid primary key default gen_random_uuid(),
  dataset_kind text not null check (dataset_kind in
    ('teams', 'players', 'player_stats', 'schedule', 'injuries', 'player_mappings')),
  season integer not null check (season between 1947 and 3000),
  status text not null default 'running' check (status in ('running', 'succeeded', 'failed')),
  snapshot_id uuid references public.fantasy_data_snapshots (id),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  -- Store a short sanitized failure code; never request headers or credentials.
  error_code text check (error_code is null or error_code ~ '^[A-Z0-9_]{1,80}$'),
  check ((status = 'running' and finished_at is null)
      or (status <> 'running' and finished_at is not null))
);

create index if not exists fantasy_snapshots_lookup_idx
  on public.fantasy_data_snapshots (dataset_kind, season, created_at desc);
create index if not exists fantasy_refresh_runs_lookup_idx
  on public.fantasy_refresh_runs (dataset_kind, season, started_at desc);

alter table public.fantasy_data_snapshots enable row level security;
alter table public.fantasy_current_datasets enable row level security;
alter table public.fantasy_refresh_runs enable row level security;

-- Explicit table privileges complement RLS. Neither visitors nor signed-in users
-- may stage data, publish snapshots, inspect refresh logs, or modify anything.
revoke all on table public.fantasy_data_snapshots,
  public.fantasy_current_datasets, public.fantasy_refresh_runs
  from public, anon, authenticated;
grant usage on schema public to anon, authenticated, service_role;
grant select on public.fantasy_data_snapshots, public.fantasy_current_datasets
  to anon, authenticated;
grant select, insert, update, delete on public.fantasy_data_snapshots,
  public.fantasy_current_datasets, public.fantasy_refresh_runs to service_role;

-- Drop/recreate only these named policies so reruns do not duplicate them.
drop policy if exists fantasy_current_public_read on public.fantasy_current_datasets;
create policy fantasy_current_public_read on public.fantasy_current_datasets
  for select to anon, authenticated using (true);

drop policy if exists fantasy_snapshot_public_read on public.fantasy_data_snapshots;
create policy fantasy_snapshot_public_read on public.fantasy_data_snapshots
  for select to anon, authenticated using (
    published_at is not null
    and exists (
      select 1 from public.fantasy_current_datasets as current_dataset
      where current_dataset.snapshot_id = fantasy_data_snapshots.id
        and current_dataset.dataset_kind = fantasy_data_snapshots.dataset_kind
        and current_dataset.season = fantasy_data_snapshots.season
    )
  );

-- No public policies are created for refresh logs. Supabase's service_role
-- bypasses RLS; keep that key strictly on the backend.

create or replace function public.fantasy_publish_snapshot(p_snapshot_id uuid)
returns uuid
language plpgsql
security invoker
set search_path = ''
as $function$
declare
  candidate public.fantasy_data_snapshots%rowtype;
  previous public.fantasy_data_snapshots%rowtype;
  item jsonb;
  numeric_key text;
  identity_key text;
  record_id text;
  seen_ids text[] := array[]::text[];
begin
  select * into candidate from public.fantasy_data_snapshots
    where id = p_snapshot_id for update;
  if not found then
    raise exception 'SNAPSHOT_NOT_FOUND' using errcode = '22023';
  end if;

  -- Serialize promotion per dataset/season; promotion itself is transactional.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(
    'fantasy:' || candidate.dataset_kind || ':' || candidate.season::text, 0));

  -- Published snapshots are immutable through this API. A new import gets a new ID.
  if candidate.published_at is not null then
    raise exception 'SNAPSHOT_ALREADY_PUBLISHED' using errcode = '22023';
  end if;
  if candidate.record_count = 0 and candidate.dataset_kind <> 'injuries' then
    raise exception 'EMPTY_DATASET' using errcode = '22023';
  end if;
  if candidate.retrieved_at > pg_catalog.clock_timestamp() + interval '5 minutes'
    or candidate.source_updated_at > pg_catalog.clock_timestamp() + interval '5 minutes' then
    raise exception 'FUTURE_DATA_TIMESTAMP' using errcode = '22023';
  end if;

  identity_key := case candidate.dataset_kind
    when 'teams' then 'team_id'
    when 'players' then 'player_id'
    when 'player_stats' then 'player_id'
    when 'schedule' then 'game_id'
    when 'injuries' then 'listing_id'
    when 'player_mappings' then 'mapping_id' end;

  for item in select value from pg_catalog.jsonb_array_elements(candidate.payload -> 'records')
  loop
    if pg_catalog.jsonb_typeof(item) <> 'object'
      or pg_catalog.jsonb_typeof(item -> identity_key) is distinct from 'string'
      or pg_catalog.btrim(item ->> identity_key) = '' then
      raise exception 'MISSING_RECORD_ID' using errcode = '22023';
    end if;
    record_id := item ->> identity_key;
    if record_id = any(seen_ids) then
      raise exception 'DUPLICATE_RECORD_ID' using errcode = '22023';
    end if;
    seen_ids := pg_catalog.array_append(seen_ids, record_id);

    if candidate.dataset_kind = 'player_stats' then
      foreach numeric_key in array array[
        'gp','pts','reb','ast','stl','blk','three_pm','fgm','fga','ftm','fta']
      loop
        if pg_catalog.jsonb_typeof(item -> numeric_key) is distinct from 'number' then
          raise exception 'MISSING_NUMERIC_STAT' using errcode = '22023';
        end if;
        if (item ->> numeric_key)::numeric < 0
          or pg_catalog.trunc((item ->> numeric_key)::numeric) <> (item ->> numeric_key)::numeric then
          raise exception 'INVALID_STAT_TOTAL' using errcode = '22023';
        end if;
      end loop;
      if (item ->> 'gp')::numeric <= 0
        or (item ->> 'fgm')::numeric > (item ->> 'fga')::numeric
        or (item ->> 'ftm')::numeric > (item ->> 'fta')::numeric
        or (item ->> 'three_pm')::numeric > (item ->> 'fgm')::numeric then
        raise exception 'INVALID_SHOOTING_OR_GAMES' using errcode = '22023';
      end if;
    elsif candidate.dataset_kind = 'schedule' then
      if pg_catalog.jsonb_typeof(item -> 'home_team_id') is distinct from 'string'
        or pg_catalog.jsonb_typeof(item -> 'away_team_id') is distinct from 'string'
        or pg_catalog.btrim(item ->> 'home_team_id') in ('', '-1', '-2', 'TBD')
        or pg_catalog.btrim(item ->> 'away_team_id') in ('', '-1', '-2', 'TBD')
        or item ->> 'home_team_id' = item ->> 'away_team_id' then
        raise exception 'UNASSIGNED_OR_INVALID_GAME' using errcode = '22023';
      end if;
      -- The importer must additionally check both IDs against the teams dataset,
      -- UTC timestamps, game status, and date-window completeness. Store TBD games
      -- separately in payload.coverage.unassigned_games, never in counted records.
    elsif candidate.dataset_kind = 'injuries' then
      if pg_catalog.jsonb_typeof(item -> 'player_id') is distinct from 'string'
        or pg_catalog.btrim(item ->> 'player_id') = ''
        or (item ->> 'status') is null
        or (item ->> 'status') not in
          ('available', 'probable', 'questionable', 'doubtful', 'out', 'unknown') then
        raise exception 'INVALID_INJURY_RECORD' using errcode = '22023';
      end if;
      -- Team reports not yet submitted belong in coverage metadata, not a fake
      -- healthy-player record. Retain report/game timestamps in each listing.
    end if;
  end loop;

  select snapshots.* into previous from public.fantasy_current_datasets as current_dataset
    join public.fantasy_data_snapshots as snapshots on snapshots.id = current_dataset.snapshot_id
    where current_dataset.dataset_kind = candidate.dataset_kind
      and current_dataset.season = candidate.season;

  if found then
    -- Demo/imported data must not silently replace a live dataset.
    if previous.data_mode = 'live' and candidate.data_mode <> 'live' then
      raise exception 'LIVE_DATA_REPLACEMENT_REJECTED' using errcode = '22023';
    end if;
    if candidate.retrieved_at < previous.retrieved_at
      or (previous.source_updated_at is not null and candidate.source_updated_at is null)
      or candidate.source_updated_at < previous.source_updated_at then
      raise exception 'OLDER_SNAPSHOT_REJECTED' using errcode = '22023';
    end if;
  end if;

  update public.fantasy_data_snapshots
    set published_at = pg_catalog.clock_timestamp() where id = candidate.id;
  insert into public.fantasy_current_datasets (dataset_kind, season, snapshot_id, updated_at)
    values (candidate.dataset_kind, candidate.season, candidate.id, pg_catalog.clock_timestamp())
    on conflict (dataset_kind, season) do update
      set snapshot_id = excluded.snapshot_id, updated_at = excluded.updated_at;
  return candidate.id;
end;
$function$;

-- PostgreSQL normally grants function execution to PUBLIC: explicitly remove it.
revoke all on function public.fantasy_publish_snapshot(uuid)
  from public, anon, authenticated;
grant execute on function public.fantasy_publish_snapshot(uuid) to service_role;

comment on table public.fantasy_data_snapshots is
  'Versioned public basketball datasets. Visitors can read only the current published snapshot.';
comment on table public.fantasy_current_datasets is
  'Atomic current-version pointers by dataset kind and ending-year season.';
comment on table public.fantasy_refresh_runs is
  'Backend-only sanitized refresh outcomes. Failed refreshes must leave current pointers unchanged.';
comment on function public.fantasy_publish_snapshot(uuid) is
  'Backend-only validation and atomic publication. Does not independently establish provider rights or complete coverage.';

notify pgrst, 'reload schema';
commit;

-- Success check: returns three rows with row_security_enabled = true.
select tablename, rowsecurity as row_security_enabled
from pg_catalog.pg_tables
where schemaname = 'public'
  and tablename in ('fantasy_data_snapshots', 'fantasy_current_datasets', 'fantasy_refresh_runs')
order by tablename;
