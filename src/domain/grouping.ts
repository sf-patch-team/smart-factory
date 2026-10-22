import type { Asset, KevEntry } from "./types";

export type RiskItem = { asset: Asset; entry: KevEntry; score: number };

export type RiskGroup = {
  key: string;
  entry: KevEntry;
  assets: Asset[];
  topScore: number;
  topAsset: Asset; // 점수가 가장 높은 자산(화면에 대표로 보인다)
};

function normalize(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "");
}

// 같은 제품·버전을 쓰는 자산은 같은 취약점을 한 번에 확인한다(FR-25).
// KEV에 버전이 없어서 후보가 자산 수만큼 불어나는 것을 줄이려는 규칙이다.
export function groupKey(asset: Asset, entry: KevEntry): string {
  return [normalize(asset.vendor), normalize(asset.product), normalize(asset.version), entry.cveId].join("|");
}

export function groupRisks(items: RiskItem[]): RiskGroup[] {
  const groups = new Map<string, RiskGroup>();
  for (const { asset, entry, score } of items) {
    const key = groupKey(asset, entry);
    const group = groups.get(key);
    if (!group) {
      groups.set(key, { key, entry, assets: [asset], topScore: score, topAsset: asset });
      continue;
    }
    group.assets.push(asset);
    if (score > group.topScore) {
      group.topScore = score;
      group.topAsset = asset;
    }
  }
  return [...groups.values()].sort((a, b) => b.topScore - a.topScore);
}

// 기본으로 상위 N건만 보여 주고 나머지는 접는다(FR-22).
export function topGroups(groups: RiskGroup[], limit: number): { shown: RiskGroup[]; hiddenCount: number } {
  return { shown: groups.slice(0, limit), hiddenCount: Math.max(0, groups.length - limit) };
}
