import type { AssetEvent, ChangeEvent, ChangeRisk, EventImpact, IncidentEvent } from "@/domain/history";
import type { Asset } from "@/domain/types";
import stats2013 from "./data/bpi2013-stats.json";
import stats2014 from "./data/bpi2014-stats.json";

// 가상 과거 이력(장애·변경). BPI 2013·2014의 **집계 통계**(분포)로 만든 새 데이터이며,
// 원본 행·이름·번호는 쓰지 않는다. 출처와 가정은 docs/data-sources.md.

export type { AssetEvent, ChangeEvent, ChangeRisk, EventImpact, IncidentEvent } from "@/domain/history";
export type AssetClass = "computer" | "network" | "application" | "device";

type Quantiles = Record<string, number>;
const MS_PER_DAY = 86_400_000;
const MAX_INCIDENTS_PER_YEAR = 25;
const MAX_CHANGES_PER_YEAR = 20;
const QUANTILE_POINTS: [number, string][] = [
  [0.1, "p10"], [0.25, "p25"], [0.5, "p50"], [0.75, "p75"], [0.9, "p90"], [0.99, "p99"],
];

// 고정 난수(seed)라서 같은 입력이면 항상 같은 결과가 나온다.
export function createRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// 분위수 표(p10~p99)를 선형으로 이어서 값을 뽑는다. cap으로 극단값을 막는다.
export function sampleQuantiles(table: Quantiles, random: () => number, cap = Infinity): number {
  const u = random();
  const points: [number, number][] = [[0, 0], ...QUANTILE_POINTS.map(([p, key]): [number, number] => [p, table[key]])];
  points.push([1, Math.min(table.max ?? table.p99, cap)]);
  for (let i = 1; i < points.length; i++) {
    const [p0, v0] = points[i - 1];
    const [p1, v1] = points[i];
    if (u > p1) continue;
    const t = (u - p0) / (p1 - p0);
    // 꼬리가 긴 분포라서 값이 모두 양수인 구간은 곱셈(로그) 방식으로 이어야 윗구간이 부풀지 않는다.
    const value = v0 > 0 && v1 > 0 ? v0 * (v1 / v0) ** t : v0 + t * (v1 - v0);
    return Math.min(cap, value);
  }
  return Math.min(cap, points[points.length - 1][1]);
}

function pick<T extends string>(shares: Record<string, number>, random: () => number, map: (key: string) => T): T {
  let u = random();
  const entries = Object.entries(shares);
  for (const [key, share] of entries) {
    u -= share;
    if (u <= 0) return map(key);
  }
  return map(entries[0][0]);
}

// BPI에 대응하는 설비 유형이 없는 제어 장비(PLC 등)는 hardware 수치를 임시로 쓴다(docs/data-sources.md).
export function assetClass(assetType: string): AssetClass {
  if (/PC|서버|SCADA/.test(assetType)) return "computer";
  if (/스위치|방화벽|라우터|보안장비|VPN|SMA|게이트웨이/.test(assetType)) return "network";
  if (/소프트웨어/.test(assetType)) return "application";
  return "device";
}

const BPI_TYPE_OF_CLASS: Record<AssetClass, string> = {
  computer: "computer", network: "networkcomponents", application: "application", device: "hardware",
};

function incidentFactor(cls: AssetClass): number {
  const byType = stats2014.incidents.mean_incidents_per_ci_by_type as Record<string, number>;
  const mean = stats2014.incidents.incidents_per_ci.mean;
  return Math.min(3, Math.max(0.2, (byType[BPI_TYPE_OF_CLASS[cls]] ?? mean) / mean));
}

function dayOffset(today: string, random: () => number): string {
  const date = new Date(Date.parse(today) - Math.floor(random() * 365) * MS_PER_DAY);
  return date.toISOString().slice(0, 10);
}

const yearScale = 365 / (stats2014.incidents.period_days ?? 365);

function makeIncident(asset: Asset, today: string, random: () => number): IncidentEvent {
  const inc = stats2014.incidents;
  return {
    kind: "incident",
    assetId: asset.id,
    openedAt: dayOffset(today, random),
    resolvedAfterDays: Math.round(sampleQuantiles(inc.open_to_resolved_days, random, 60) * 10) / 10,
    handleHours: Math.round(sampleQuantiles(inc.handle_time_hours, random, 200) * 10) / 10,
    reassignments: Math.round(sampleQuantiles(inc.reassignments, random, 10)),
    impact: pick(stats2013.impact_first_event, random, (key) => (key === "Low" ? "low" : key === "Medium" ? "medium" : "high")),
  };
}

function makeChange(asset: Asset, today: string, random: () => number): ChangeEvent {
  const chg = stats2014.changes;
  const risk = pick(chg.risk_assessment, random, (key) =>
    key === "Minor Change" ? "minor" : key === "Business Change" ? "business" : "major");
  const hasWindow = asset.patchConstraints.includes("maintenance_window");
  const hasDowntime = hasWindow || random() < chg.share_with_scheduled_downtime; // 점검 창이 있는 자산은 계획 중단을 둔다(우리 가정)
  const related = (chg.related_incident_share_by_risk as Record<string, { share_with_incident: number }>)[
    risk === "minor" ? "Minor Change" : risk === "business" ? "Business Change" : "Major Business Change"];
  return {
    kind: "change",
    assetId: asset.id,
    startedAt: dayOffset(today, random),
    risk,
    emergency: random() < (chg.emergency.Y ?? 0),
    cabNeeded: random() < (chg.cab_needed.Y ?? 0),
    plannedDowntimeMinutes: hasDowntime ? Math.round(sampleQuantiles(chg.scheduled_downtime_minutes, random, 1440)) : 0,
    actualDurationMinutes: Math.round(sampleQuantiles(chg.actual_duration_minutes, random, 1440)),
    hadRelatedIncident: random() < related.share_with_incident,
  };
}

export function buildAssetHistory(assets: Asset[], today: string, seed = 2026): AssetEvent[] {
  const random = createRandom(seed);
  const events: AssetEvent[] = [];
  for (const asset of assets) {
    const incidents = Math.min(
      MAX_INCIDENTS_PER_YEAR,
      Math.round(sampleQuantiles(stats2014.incidents.incidents_per_ci, random, 400) * yearScale * incidentFactor(assetClass(asset.assetType))),
    );
    const changes = Math.min(MAX_CHANGES_PER_YEAR, Math.round(sampleQuantiles(stats2014.changes.changes_per_ci, random, 60) * yearScale));
    for (let i = 0; i < incidents; i++) events.push(makeIncident(asset, today, random));
    for (let i = 0; i < changes; i++) events.push(makeChange(asset, today, random));
  }
  return events;
}
