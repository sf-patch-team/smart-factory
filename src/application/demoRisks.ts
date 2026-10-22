import { groupRisks, type RiskGroup } from "@/domain/grouping";
import { findCandidates } from "@/domain/matching";
import { computeScore, type Score } from "@/domain/scoring";
import type { Asset, KevEntry } from "@/domain/types";

export type RiskRow = { asset: Asset; entry: KevEntry; score: Score };
export type RiskGroupRow = { group: RiskGroup; score: Score };

// 뼈대용: DB 없이 가상 자산 × KEV로 위험 목록을 만든다(시험 모드와 같은 흐름, FR-20).
export function buildRiskRows(assets: Asset[], entries: KevEntry[], today: string): RiskRow[] {
  return assets
    .flatMap((asset) =>
      findCandidates(asset, entries).map((entry) => ({
        asset,
        entry,
        score: computeScore(asset, entry, today),
      })),
    )
    .sort((a, b) => b.score.total - a.score.total);
}

// 같은 제품·버전 자산을 묶어 보여 준다(FR-25). 묶음의 점수는 가장 높은 자산 기준이다.
export function buildRiskGroups(assets: Asset[], entries: KevEntry[], today: string): RiskGroupRow[] {
  const rows = buildRiskRows(assets, entries, today);
  const groups = groupRisks(rows.map((row) => ({ asset: row.asset, entry: row.entry, score: row.score.total })));
  return groups.map((group) => ({ group, score: computeScore(group.topAsset, group.entry, today) }));
}
