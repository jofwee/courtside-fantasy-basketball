import test from "node:test";
import assert from "node:assert/strict";
import { aggregate, blankScenario, delta, makeValueModel, postTradeIds, scheduleCounts, suggestions, validate, type Player, type Scenario } from "../lib/basketball";
const player = (id: string, overrides = {}): Player => ({ id, name: id, teamId: "1", team: "ATL", position: "G", totals: { gp: 1, pts: 10, reb: 3, ast: 4, stl: 1, blk: 0, three_pm: 0, fgm: 5, fga: 10, ftm: 0, fta: 0, ...overrides } });
test("shooting percentages use attempts, not simple player percentage averages", () => {
  const result = aggregate([player("a"), player("b", { fgm: 1, fga: 1 })]);
  assert.ok(Math.abs(result.fg_pct! - 6 / 11 * 100) < 1e-9);
  assert.equal(result.ft_pct, null);
});
test("per-game aggregation respects unequal games played", () => {
  const result = aggregate([player("a", { gp: 10, pts: 200 }), player("b", { gp: 2, pts: 20 })]);
  assert.equal(result.pts, 30);
});
test("missing statistics never become zero production", () => {
  const p = player("a"); delete p.totals;
  assert.ok(Object.values(aggregate([p])).every(value => value === null));
});
test("schedule-weighted percentages apply game counts to makes and attempts", () => {
  const result = aggregate([player("a"), player("b", { fgm: 1, fga: 1 })], new Map([["a", 3], ["b", 1]]));
  assert.ok(Math.abs(result.fg_pct! - 16 / 31 * 100) < 1e-9);
});
test("uneven trades require actual drops to fit the roster", () => {
  const all = Array.from({ length: 15 }, (_, i) => player(String(i)));
  const scenario: Scenario = { ...blankScenario(), roster: all.slice(0, 13).map(p => p.id), give: ["0"], receive: ["13", "14"] };
  assert.equal(postTradeIds(scenario).length, 14);
  assert.ok(validate(scenario, new Map(all.map(p => [p.id, p]))).some(x => x.includes("Choose who to drop")));
  scenario.drops = ["1"];
  assert.deepEqual(validate(scenario, new Map(all.map(p => [p.id, p]))), []);
  assert.equal(postTradeIds(scenario).length, 13);
});
test("owned incoming players and overlapping packages are rejected", () => {
  const all = [player("a"), player("b")];
  const s = { ...blankScenario(), roster: ["a", "b"], give: ["a"], receive: ["a"] };
  const errors = validate(s, new Map(all.map(p => [p.id, p])));
  assert.ok(errors.some(e => e.includes("both sides")));
  assert.ok(errors.some(e => e.includes("already on")));
});
test("trade-only mode does not require a roster", () => {
  const all = [player("a"), player("b")];
  assert.deepEqual(validate({ ...blankScenario(), tradeOnly: true, give: ["a"], receive: ["b"] }, new Map(all.map(p => [p.id, p]))), []);
});
test("a trade followed by its reversal restores all roster categories", () => {
  const a = player("a"), b = player("b", { pts: 25, fgm: 10, fga: 18 });
  const original = aggregate([a]);
  const forward = delta(original, aggregate([b])), backward = delta(aggregate([b]), original);
  for (const key of Object.keys(forward) as (keyof typeof forward)[]) if (forward[key] !== null) assert.equal(forward[key]! + backward[key]!, 0);
});
test("scheduled games respect timezone boundaries and ignore postponed games", () => {
  const p = player("a");
  const games = [
    { game_id: "1", home_team_id: "1", away_team_id: "2", starts_at: "2026-11-09T23:30:00Z", status: "STATUS_SCHEDULED" },
    { game_id: "2", home_team_id: "1", away_team_id: "2", starts_at: "2026-11-10T12:00:00Z", status: "STATUS_POSTPONED" },
  ];
  assert.equal(scheduleCounts([p], games, "2026-11-10", 1, "Asia/Manila").get("a"), 1);
  assert.equal(scheduleCounts([p], games, "2026-11-10", 1, "UTC").get("a"), 0);
});
test("turnovers have no influence on category values", () => {
  const p = player("a", { gp: 5, pts: 100 });
  const model = makeValueModel([p]);
  const before = model.score(p);
  (p.totals as unknown as Record<string, number>).turnovers = 999;
  assert.equal(model.score(p), before);
});
test("counteroffers respect candidate restrictions and avoid owned players", () => {
  const pool = Array.from({ length: 15 }, (_, i) => player(String(i), { gp: 5, pts: 20 + i * 8, fgm: i + 2, fga: i + 8 }));
  const s = { ...blankScenario(), roster: ["0", "1"], give: ["0"], receive: ["2"] };
  const result = suggestions(s, pool, ["5", "6"]);
  assert.ok(result.length > 0);
  assert.ok(result.every(r => r.receive.every(id => ["5", "6"].includes(id))));
});
