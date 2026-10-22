import { describe, expect, it } from "vitest";
import { computeScore } from "@/domain/scoring";
import { findCandidates, isCandidate } from "@/domain/matching";
import { SEED_ASSETS } from "@/infrastructure/seed/assets";
import { TEST_KEV_ENTRIES } from "@/infrastructure/seed/testKev";
import type { Asset, KevEntry } from "@/domain/types";

const TODAY = "2026-10-22";

const asset = (over: Partial<Asset> = {}): Asset => ({
  id: "a1", name: "test", vendor: "Fortinet", product: "FortiOS", version: "7.2",
  category: "IT", assetType: "방화벽", zone: "경계망", line: "외부 연결",
  criticality: "mid", affectedEquipment: "x", patchConstraints: [], rollbackPossible: true,
  ...over,
});

const kev = (over: Partial<KevEntry> = {}): KevEntry => ({
  cveId: "TEST-9999", vendorProject: "Fortinet", product: "FortiOS", vulnerabilityName: "n",
  dateAdded: "2026-10-01", dueDate: "2026-10-08", ransomwareKnown: false, shortDescription: "", requiredAction: "",
  ...over,
});

describe("scoring (R-09, S-07)", () => {
  it("점수 구성 4개 항목을 합쳐 총점을 낸다", () => {
    const score = computeScore(asset({ criticality: "high" }), kev({ ransomwareKnown: true }), TODAY);
    const { overdue, ransomware, criticality, recency } = score.breakdown;
    expect(score.total).toBe(overdue + ransomware + criticality + recency);
    expect(ransomware).toBe(25);
    expect(criticality).toBe(25);
    expect(score.overdueDays).toBe(14);
  });

  it("기한이 아직 안 지났으면 기한 초과 점수는 0이다", () => {
    const score = computeScore(asset(), kev({ dueDate: "2026-11-30" }), TODAY);
    expect(score.breakdown.overdue).toBe(0);
    expect(score.overdueDays).toBe(0);
  });

  it("기한 초과 점수는 상한이 있어 한 항목이 지배하지 않는다", () => {
    const score = computeScore(asset(), kev({ dueDate: "2020-01-01" }), TODAY);
    expect(score.breakdown.overdue).toBe(40);
  });

  it("중요도가 높을수록 총점이 높다", () => {
    const high = computeScore(asset({ criticality: "high" }), kev(), TODAY).total;
    const low = computeScore(asset({ criticality: "low" }), kev(), TODAY).total;
    expect(high).toBeGreaterThan(low);
  });
});

describe("matching (R-07, S-06, ADR 0001)", () => {
  it("대소문자와 회사 접미어가 달라도 벤더·제품이 같으면 후보다", () => {
    expect(isCandidate(asset({ vendor: "FORTINET Inc.", product: "fortios" }), kev())).toBe(true);
  });

  it("제품이 다르면 후보가 아니다", () => {
    expect(isCandidate(asset({ product: "FortiMail" }), kev())).toBe(false);
  });

  it("벤더가 다르면 후보가 아니다", () => {
    expect(isCandidate(asset({ vendor: "Moxa", product: "EDS-508A" }), kev())).toBe(false);
  });

  it("KEV가 'Multiple Products'면 벤더만 맞아도 후보다", () => {
    const rockwell = asset({ vendor: "Rockwell Automation", product: "FactoryTalk View" });
    expect(isCandidate(rockwell, kev({ vendorProject: "Rockwell", product: "Multiple Products" }))).toBe(true);
  });

  it("너무 짧은 이름은 우연히 겹치지 않는다", () => {
    expect(isCandidate(asset({ vendor: "AB", product: "X" }), kev({ vendorProject: "ABB", product: "XY" }))).toBe(false);
  });

  it("가상 자산 중 일부만 시험용 KEV와 맞는다", () => {
    const matched = SEED_ASSETS.filter((a) => findCandidates(a, TEST_KEV_ENTRIES).length > 0);
    expect(matched.length).toBeGreaterThan(0);
    expect(matched.length).toBeLessThan(SEED_ASSETS.length);
  });

  it("벤더만 같고 제품이 다른 설비(Schneider Modicon)는 후보가 아니다", () => {
    const modicon = SEED_ASSETS.find((a) => a.product === "Modicon M580")!;
    expect(findCandidates(modicon, TEST_KEV_ENTRIES)).toHaveLength(0);
  });
});
