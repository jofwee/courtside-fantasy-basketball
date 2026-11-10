export const CATEGORIES = [
  { key: "pts", label: "PTS", name: "Points", percent: false },
  { key: "reb", label: "REB", name: "Rebounds", percent: false },
  { key: "ast", label: "AST", name: "Assists", percent: false },
  { key: "stl", label: "STL", name: "Steals", percent: false },
  { key: "blk", label: "BLK", name: "Blocks", percent: false },
  { key: "three_pm", label: "3PM", name: "Three-pointers made", percent: false },
  { key: "fg_pct", label: "FG%", name: "Field goal percentage", percent: true },
  { key: "ft_pct", label: "FT%", name: "Free throw percentage", percent: true },
] as const;
export type Category = typeof CATEGORIES[number]["key"];
export type Profile = Record<Category, number | null>;
export type Totals = { gp: number; pts: number; reb: number; ast: number; stl: number; blk: number; three_pm: number; fgm: number; fga: number; ftm: number; fta: number; three_pa?: number };
export type Player = { id: string; name: string; teamId: string; team: string; position: string; totals?: Totals };
export type Game = { game_id: string; home_team_id: string; away_team_id: string; starts_at: string; status: string };
export type Injury = { listing_id: string; player_id: string; status: string; game_date: string; report_local: string; report_timezone: string };
export type Dataset = { players: Player[]; games: Game[]; injuries: Injury[]; season: number; retrievedAt: string; dataMode: string; injuryReport: string | null; unassigned: { game_id: string; date: string }[]; snapshotIds: string[]; warnings: string[] };
export type Scenario = { roster: string[]; give: string[]; receive: string[]; drops: string[]; replacements: string[]; focus: Category[]; excluded: string[]; tradeOnly: boolean; example: boolean };

export function aggregate(players: Player[], multipliers?: Map<string, number>): Profile {
  const result: Profile = { pts: 0, reb: 0, ast: 0, stl: 0, blk: 0, three_pm: 0, fg_pct: null, ft_pct: null };
  let fgm = 0, fga = 0, ftm = 0, fta = 0;
  if (players.some(p => !p.totals || p.totals.gp <= 0)) return Object.fromEntries(CATEGORIES.map(c => [c.key, null])) as Profile;
  for (const p of players) {
    const t = p.totals!;
    const weight = (multipliers?.get(p.id) ?? (multipliers ? 0 : 1)) / t.gp;
    for (const c of CATEGORIES) if (!c.percent) result[c.key]! += t[c.key as keyof Totals]! * weight;
    fgm += t.fgm * weight; fga += t.fga * weight; ftm += t.ftm * weight; fta += t.fta * weight;
  }
  result.fg_pct = fga ? fgm / fga * 100 : null;
  result.ft_pct = fta ? ftm / fta * 100 : null;
  return result;
}

export function delta(before: Profile, after: Profile): Profile {
  return Object.fromEntries(CATEGORIES.map(({ key }) => [key, before[key] === null || after[key] === null ? null : after[key]! - before[key]!])) as Profile;
}

export function format(value: number | null | undefined, percent = false) {
  return value === null || value === undefined || !Number.isFinite(value) ? "—" : `${value.toFixed(1)}${percent ? "%" : ""}`;
}

export function validate(s: Scenario, players: Map<string, Player>): string[] {
  const errors: string[] = [];
  const all = [...s.roster, ...s.give, ...s.receive, ...s.drops, ...s.replacements];
  if (all.some(id => !players.has(id))) errors.push("Some saved players are no longer in this player directory. Remove them to continue.");
  for (const [label, ids] of [["roster", s.roster], ["outgoing package", s.give], ["incoming package", s.receive], ["drops", s.drops], ["replacements", s.replacements]] as const) {
    if (new Set(ids).size !== ids.length) errors.push(`Remove duplicate players from your ${label}.`);
  }
  if (!s.give.length || !s.receive.length) errors.push("Add at least one player to each side of the trade.");
  if (s.give.some(id => s.receive.includes(id))) errors.push("A player cannot appear on both sides of the trade.");
  if (s.roster.length > 13) errors.push("Your starting roster can have up to 13 players.");
  if (!s.tradeOnly) {
    if (!s.roster.length) errors.push("Add your roster, or turn on trade-only mode.");
    if (s.give.some(id => !s.roster.includes(id))) errors.push("Choose outgoing players from your roster.");
    if (s.receive.some(id => s.roster.includes(id))) errors.push("An incoming player is already on your roster.");
    if (s.drops.some(id => !s.roster.includes(id) || s.give.includes(id))) errors.push("Drop choices must be remaining roster players.");
    if (s.replacements.some(id => s.roster.includes(id) || s.receive.includes(id) || s.give.includes(id))) errors.push("Choose a replacement you do not already own or trade.");
    if (postTradeIds(s).length > 13) errors.push(`Your new roster would have ${postTradeIds(s).length} players. Choose who to drop below.`);
  }
  return errors;
}

export function postTradeIds(s: Scenario) {
  return [...s.roster.filter(id => !s.give.includes(id) && !s.drops.includes(id)), ...s.receive, ...s.replacements];
}

export function makeValueModel(players: Player[], focus: Category[] = []) {
  const pool = players.filter(p => p.totals && p.totals.gp >= 5);
  const baseline = aggregate(pool);
  const vector = (p: Player): Record<Category, number> | null => {
    if (!p.totals || p.totals.gp <= 0) return null;
    const t = p.totals, rate = aggregate([p]);
    return {
      pts: rate.pts!, reb: rate.reb!, ast: rate.ast!, stl: rate.stl!, blk: rate.blk!, three_pm: rate.three_pm!,
      fg_pct: (t.fgm - (baseline.fg_pct ?? 0) / 100 * t.fga) / t.gp,
      ft_pct: (t.ftm - (baseline.ft_pct ?? 0) / 100 * t.fta) / t.gp,
    };
  };
  const vectors = pool.map(p => vector(p)!);
  const means = {} as Record<Category, number>, spreads = {} as Record<Category, number>;
  for (const { key } of CATEGORIES) {
    means[key] = vectors.length ? vectors.reduce((sum, v) => sum + v[key], 0) / vectors.length : 0;
    spreads[key] = vectors.length ? Math.sqrt(vectors.reduce((sum, v) => sum + (v[key] - means[key]) ** 2, 0) / vectors.length) : 0;
  }
  const raw = (p: Player) => {
    const v = vector(p);
    if (!v) return null;
    return CATEGORIES.reduce((sum, { key }) => sum + (spreads[key] ? (v[key] - means[key]) / spreads[key] : 0) * (focus.includes(key) ? 2 : 1), 0);
  };
  const ordered = pool.map(p => raw(p)!).sort((a, b) => b - a);
  const replacement = ordered[Math.min(129, Math.max(0, ordered.length - 1))] ?? 0;
  return {
    poolSize: pool.length,
    score: (p: Player) => { const n = raw(p); return n === null ? null : n - replacement; },
    packageScore: (packagePlayers: Player[]) => packagePlayers.some(p => raw(p) === null) ? null : packagePlayers.reduce((sum, p) => sum + raw(p)! - replacement, 0),
  };
}

const dateFormatters = new Map<string, Intl.DateTimeFormat>();
export function dayInZone(value: string | Date, zone: string) {
  let formatter = dateFormatters.get(zone);
  if (!formatter) { formatter = new Intl.DateTimeFormat("en-CA", { timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit" }); dateFormatters.set(zone, formatter); }
  const parts = formatter.formatToParts(new Date(value));
  const get = (name: string) => parts.find(p => p.type === name)?.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}

export function scheduleCounts(players: Player[], games: Game[], start: string, days: number, zone: string) {
  const end = new Date(start + "T00:00:00Z"); end.setUTCDate(end.getUTCDate() + days);
  const last = end.toISOString().slice(0, 10);
  const byTeam = new Map<string, number>();
  for (const game of games) {
    if (game.status !== "STATUS_SCHEDULED") continue;
    const day = dayInZone(game.starts_at, zone);
    if (day < start || day >= last) continue;
    for (const team of [game.home_team_id, game.away_team_id]) byTeam.set(team, (byTeam.get(team) ?? 0) + 1);
  }
  return new Map(players.map(p => [p.id, byTeam.get(p.teamId) ?? 0]));
}

export function suggestions(s: Scenario, players: Player[], candidates: string[] = []) {
  const lookup = new Map(players.map(p => [p.id, p]));
  const resolve = (ids: string[]) => ids.map(id => lookup.get(id)).filter((p): p is Player => Boolean(p));
  const model = makeValueModel(players, s.focus), give = resolve(s.give);
  const target = model.packageScore(give);
  if (target === null || !s.receive.length || !s.give.length) return [];
  const excluded = new Set([...s.roster, ...s.give, ...s.receive, ...s.replacements]);
  const pool = players.filter(p => !excluded.has(p.id) && p.totals && p.totals.gp >= 5 && (!candidates.length || candidates.includes(p.id)))
    .sort((a, b) => (model.score(b) ?? -Infinity) - (model.score(a) ?? -Infinity)).slice(0, 180);
  const offers: { receive: string[]; balance: number; value: number }[] = [];
  for (const p of pool) for (let i = 0; i < s.receive.length; i++) {
    const ids = s.receive.map((id, index) => index === i ? p.id : id);
    const value = model.packageScore(resolve(ids));
    if (value !== null && new Set(ids).size === ids.length) offers.push({ receive: ids, balance: Math.abs(value - target), value });
  }
  return offers.sort((a, b) => a.balance - b.balance || b.value - a.value).slice(0, 3);
}

export function exampleScenario(players: Player[]): Scenario {
  const withStats = players.filter(p => p.totals);
  const names = ["Luka Doncic", "Devin Booker", "Mikal Bridges", "Aaron Gordon", "Bam Adebayo", "Derrick White", "Myles Turner", "Josh Hart", "Austin Reaves", "Jarrett Allen", "Naz Reid", "Alex Caruso", "Al Horford"];
  const incoming = withStats.find(p => p.name === "Giannis Antetokounmpo");
  const roster = names.map(name => withStats.find(p => p.name === name)).filter((p): p is Player => Boolean(p) && p?.id !== incoming?.id);
  for (const p of withStats) if (roster.length < 13 && !roster.includes(p) && p.id !== incoming?.id) roster.push(p);
  const outgoing = roster.find(p => p.name === "Luka Doncic") ?? roster[0];
  return { roster: roster.map(p => p.id), give: outgoing ? [outgoing.id] : [], receive: incoming ? [incoming.id] : [], drops: [], replacements: [], focus: [], excluded: [], tradeOnly: false, example: true };
}

export function blankScenario(): Scenario {
  return { roster: [], give: [], receive: [], drops: [], replacements: [], focus: [], excluded: [], tradeOnly: false, example: false };
}
