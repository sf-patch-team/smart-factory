import { findCandidates } from "@/domain/matching";
import { computeScore, type Score } from "@/domain/scoring";
import type { Asset, KevEntry } from "@/domain/types";

export type RiskRow = { asset: Asset; entry: KevEntry; score: Score };

// 뼈대용: DB 없이 가상 자산 × 시험용 KEV로 위험 목록을 만든다(시험 모드와 같은 흐름, FR-20).
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
