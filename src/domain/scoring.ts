import type { Asset, KevEntry } from "./types";

export type ScoreBreakdown = {
  overdue: number;
  ransomware: number;
  criticality: number;
  recency: number;
};

export type Score = { total: number; breakdown: ScoreBreakdown; overdueDays: number };

// 가정(spec Q-01): 합계 최대 100. 가중치는 팀 검토 뒤 조정한다.
const CRITICALITY_POINTS = { high: 25, mid: 15, low: 5 } as const;
const MAX_OVERDUE_POINTS = 40;
const OVERDUE_CAP_DAYS = 365;
const RANSOMWARE_POINTS = 25;
const MS_PER_DAY = 86_400_000;

function daysBetween(from: string, to: string): number {
  return Math.floor((Date.parse(to) - Date.parse(from)) / MS_PER_DAY);
}

function overduePoints(overdueDays: number): number {
  if (overdueDays <= 0) return 0;
  const capped = Math.min(overdueDays, OVERDUE_CAP_DAYS);
  return Math.round((capped / OVERDUE_CAP_DAYS) * MAX_OVERDUE_POINTS);
}

function recencyPoints(daysSinceAdded: number): number {
  if (daysSinceAdded <= 30) return 10;
  if (daysSinceAdded <= 90) return 5;
  return 0;
}

export function computeScore(asset: Asset, entry: KevEntry, today: string): Score {
  const overdueDays = daysBetween(entry.dueDate, today);
  const breakdown: ScoreBreakdown = {
    overdue: overduePoints(overdueDays),
    ransomware: entry.ransomwareKnown ? RANSOMWARE_POINTS : 0,
    criticality: CRITICALITY_POINTS[asset.criticality],
    recency: recencyPoints(daysBetween(entry.dateAdded, today)),
  };
  const total = breakdown.overdue + breakdown.ransomware + breakdown.criticality + breakdown.recency;
  return { total, breakdown, overdueDays: Math.max(overdueDays, 0) };
}
