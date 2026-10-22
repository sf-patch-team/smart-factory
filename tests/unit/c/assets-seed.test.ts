import { describe, expect, it } from "vitest";
import { findCandidates } from "@/domain/matching";
import { SEED_ASSETS } from "@/infrastructure/seed/assets";
import { TEST_KEV_ENTRIES } from "@/infrastructure/seed/testKev";

const TODAY = "2026-10-22";

describe("가상 자산 (R-22, S-06)", () => {
  it("자산이 100개 이상이고 ID와 이름이 겹치지 않는다", () => {
    expect(SEED_ASSETS.length).toBeGreaterThanOrEqual(100);
    expect(new Set(SEED_ASSETS.map((a) => a.id)).size).toBe(SEED_ASSETS.length);
    expect(new Set(SEED_ASSETS.map((a) => a.name)).size).toBe(SEED_ASSETS.length);
  });

  it("모든 자산에 구역·라인·종류가 있고 구역이 8개 이상이다", () => {
    expect(SEED_ASSETS.every((a) => a.zone && a.line && a.assetType)).toBe(true);
    expect(new Set(SEED_ASSETS.map((a) => a.zone)).size).toBeGreaterThanOrEqual(8);
  });

  it("OT 자산 대부분은 패치 제약이 있고, 시험용 KEV와 맞는 자산이 일부 있다", () => {
    const ot = SEED_ASSETS.filter((a) => a.category === "OT");
    const constrained = ot.filter((a) => a.patchConstraints.length > 0);
    expect(constrained.length / ot.length).toBeGreaterThan(0.8);
    const matched = SEED_ASSETS.filter((a) => findCandidates(a, TEST_KEV_ENTRIES).length > 0);
    expect(matched.length).toBeGreaterThan(20);
  });

  it("실제 회사·개인 이름이 아닌 가상 구조(구역→라인)로 만든다", () => {
    expect(SEED_ASSETS.every((a) => a.name.startsWith(a.line))).toBe(true);
  });

  it("OT와 IT가 모두 있다", () => {
    expect(SEED_ASSETS.some((a) => a.category === "OT")).toBe(true);
    expect(SEED_ASSETS.some((a) => a.category === "IT")).toBe(true);
  });
});
