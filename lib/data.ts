import "server-only";
import type { Dataset, Game, Injury, Player, Totals } from "./basketball";

type Snapshot = { id: string; dataset_kind: string; retrieved_at: string; source_updated_at: string | null; payload: { records: Record<string, unknown>[]; coverage?: Record<string, unknown>; warnings?: string[] }; };
export async function loadDataset(): Promise<Dataset> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) throw new Error("Missing local database configuration");
  const response = await fetch(`${url}/rest/v1/fantasy_data_snapshots?season=eq.2027&dataset_kind=in.(players,player_stats,schedule,injuries)&select=id,dataset_kind,retrieved_at,source_updated_at,payload`, {
    headers: { apikey: key }, next: { revalidate: 120 }, signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error("The basketball dataset could not be loaded");
  const snapshots: Snapshot[] = await response.json();
  const find = (kind: string) => snapshots.find(s => s.dataset_kind === kind);
  const directory = find("players"), stats = find("player_stats");
  if (!directory || !stats) throw new Error("The player directory has not been imported yet");
  const totals = new Map(stats.payload.records.map(r => [String(r.player_id), r as unknown as Totals]));
  const players: Player[] = directory.payload.records.map(r => ({ id: String(r.player_id), name: String(r.display_name), teamId: String(r.team_id ?? ""), team: String(r.team ?? "—"), position: String(r.position ?? "—"), totals: totals.get(String(r.player_id)) }));
  return { players, games: (find("schedule")?.payload.records ?? []) as unknown as Game[], injuries: (find("injuries")?.payload.records ?? []) as unknown as Injury[], season: 2027,
    retrievedAt: stats.retrieved_at, dataMode: "imported", injuryReport: String(find("injuries")?.payload.coverage?.report_local ?? "") || null,
    unassigned: (find("schedule")?.payload.coverage?.unassigned_games ?? []) as Dataset["unassigned"], snapshotIds: snapshots.map(s => s.id),
    warnings: [...new Set(snapshots.flatMap(s => s.payload.warnings ?? []))] };
}
