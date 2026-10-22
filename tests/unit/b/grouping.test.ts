import { describe, expect, it } from "vitest";
import { buildRiskGroups, buildRiskRows } from "@/application/demoRisks";
import { groupKey, groupRisks, topGroups, type RiskItem } from "@/domain/grouping";
import { SEED_ASSETS } from "@/infrastructure/seed/assets";
import { TEST_KEV_ENTRIES } from "@/infrastructure/seed/testKev";
import type { Asset, KevEntry } from "@/domain/types";

const TODAY = "2026-10-22";

const asset = (id: string, over: Partial<Asset> = {}): Asset => ({
  id, name: id, vendor: "Microsoft", product: "Windows 10 IoT", version: "21H2", category: "OT",
  assetType: "HMI PC", zone: "조립동", line: "조립 라인 1", criticality: "mid",
  affectedEquipment: "x", patchConstraints: [], rollbackPossible: false, ...over,
});

const entry = (cveId: string): KevEntry => ({
  cveId, vendorProject: "Microsoft", product: "Windows", vulnerabilityName: "n",
  dateAdded: "2026-10-01", dueDate: "2026-10-08", ransomwareKnown: false, shortDescription: "", requiredAction: "",
});

describe("groupRisks (FR-25, S-17)", () => {
  it("같은 제품·버전·취약점은 한 묶음이 되고 점수는 가장 높은 자산 기준이다", () => {
    const items: RiskItem[] = [
      { asset: asset("a"), entry: entry("CVE-1"), score: 40 },
      { asset: asset("b"), entry: entry("CVE-1"), score: 55 },
      { asset: asset("c"), entry: entry("CVE-1"), score: 45 },
    ];
    const groups = groupRisks(items);
    expect(groups).toHaveLength(1);
    expect(groups[0].assets).toHaveLength(3);
    expect(groups[0].topScore).toBe(55);
    expect(groups[0].topAsset.id).toBe("b");
  });

  it("버전이나 취약점이 다르면 따로 묶는다", () => {
    const items: RiskItem[] = [
      { asset: asset("a"), entry: entry("CVE-1"), score: 40 },
      { asset: asset("b", { version: "22H2" }), entry: entry("CVE-1"), score: 40 },
      { asset: asset("c"), entry: entry("CVE-2"), score: 40 },
    ];
    expect(groupRisks(items)).toHaveLength(3);
  });

  it("대소문자·공백 차이는 같은 키로 본다", () => {
    expect(groupKey(asset("a", { vendor: "MICROSOFT" }), entry("CVE-1"))).toBe(groupKey(asset("b"), entry("CVE-1")));
  });

  it("점수 높은 묶음이 먼저 나온다", () => {
    const items: RiskItem[] = [
      { asset: asset("a"), entry: entry("CVE-1"), score: 10 },
      { asset: asset("b"), entry: entry("CVE-2"), score: 90 },
    ];
    expect(groupRisks(items).map((g) => g.entry.cveId)).toEqual(["CVE-2", "CVE-1"]);
  });
});

describe("topGroups (FR-22, S-15)", () => {
  it("상위 N건만 보여 주고 나머지 개수를 알려 준다", () => {
    const groups = groupRisks(Array.from({ length: 12 }, (_, i) => ({ asset: asset(`a${i}`), entry: entry(`CVE-${i}`), score: i })));
    const { shown, hiddenCount } = topGroups(groups, 10);
    expect(shown).toHaveLength(10);
    expect(hiddenCount).toBe(2);
    expect(topGroups(groups, 50).hiddenCount).toBe(0);
  });
});

describe("가상 자산 × 시험용 KEV", () => {
  it("묶으면 후보 수가 줄고 자산 수는 그대로 보존된다", () => {
    const rows = buildRiskRows(SEED_ASSETS, TEST_KEV_ENTRIES, TODAY);
    const groups = buildRiskGroups(SEED_ASSETS, TEST_KEV_ENTRIES, TODAY);
    expect(groups.length).toBeLessThan(rows.length);
    const assetsInGroups = groups.reduce((sum, row) => sum + row.group.assets.length, 0);
    expect(assetsInGroups).toBe(rows.length);
  });
});
