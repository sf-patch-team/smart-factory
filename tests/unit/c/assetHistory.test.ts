import { describe, expect, it } from "vitest";
import {
  assetClass, buildAssetHistory, createRandom, sampleQuantiles,
  type ChangeEvent, type IncidentEvent,
} from "@/infrastructure/seed/assetHistory";
import { SEED_ASSETS } from "@/infrastructure/seed/assets";

const TODAY = "2026-10-22";
const history = buildAssetHistory(SEED_ASSETS, TODAY);
const incidents = history.filter((e): e is IncidentEvent => e.kind === "incident");
const changes = history.filter((e): e is ChangeEvent => e.kind === "change");

describe("sampleQuantiles (BPI 분포로 값 뽑기)", () => {
  const table = { p10: 1, p25: 2, p50: 4, p75: 8, p90: 16, p99: 100, max: 1000 };

  it("값은 0 이상이고 cap을 넘지 않는다", () => {
    const random = createRandom(1);
    for (let i = 0; i < 500; i++) {
      const value = sampleQuantiles(table, random, 50);
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThanOrEqual(50);
    }
  });

  it("중앙값 근처에 값이 모인다(분포가 표를 따른다)", () => {
    const random = createRandom(2);
    const values = Array.from({ length: 4000 }, () => sampleQuantiles(table, random)).sort((a, b) => a - b);
    expect(values[2000]).toBeGreaterThan(3);
    expect(values[2000]).toBeLessThan(5);
  });
});

describe("가상 이력 (BPI 통계 기반)", () => {
  it("같은 seed면 항상 같은 결과다", () => {
    expect(buildAssetHistory(SEED_ASSETS, TODAY, 7)).toEqual(buildAssetHistory(SEED_ASSETS, TODAY, 7));
  });

  it("장애와 변경이 모두 만들어지고 장애는 일부 자산에 몰린다(꼬리가 긴 분포)", () => {
    expect(incidents.length).toBeGreaterThan(0);
    expect(changes.length).toBeGreaterThan(0);
    const perAsset = new Map<string, number>();
    for (const e of incidents) perAsset.set(e.assetId, (perAsset.get(e.assetId) ?? 0) + 1);
    const counts = [...perAsset.values()].sort((a, b) => b - a);
    expect(Math.max(...counts)).toBeLessThanOrEqual(25);
    expect(perAsset.size).toBeLessThan(SEED_ASSETS.length); // 장애가 한 번도 없는 자산도 있다
    expect(counts[0]).toBeGreaterThan(counts[Math.floor(counts.length / 2)]);
  });

  it("변경 위험도는 BPI처럼 대부분 minor다", () => {
    const minor = changes.filter((c) => c.risk === "minor").length / changes.length;
    expect(minor).toBeGreaterThan(0.85);
    expect(minor).toBeLessThan(1);
  });

  it("점검 창이 있는 자산의 변경에는 계획된 중단 시간이 있다(우리 가정)", () => {
    const windowIds = new Set(SEED_ASSETS.filter((a) => a.patchConstraints.includes("maintenance_window")).map((a) => a.id));
    const mine = changes.filter((c) => windowIds.has(c.assetId));
    expect(mine.length).toBeGreaterThan(0);
    expect(mine.filter((c) => c.plannedDowntimeMinutes > 0).length).toBeGreaterThan(mine.length * 0.9);
  });

  it("날짜는 최근 1년 안이고 모든 이력은 존재하는 자산에 붙는다", () => {
    const ids = new Set(SEED_ASSETS.map((a) => a.id));
    const earliest = Date.parse(TODAY) - 366 * 86_400_000;
    for (const e of history) {
      expect(ids.has(e.assetId)).toBe(true);
      const date = Date.parse(e.kind === "incident" ? e.openedAt : e.startedAt);
      expect(date).toBeGreaterThanOrEqual(earliest);
      expect(date).toBeLessThanOrEqual(Date.parse(TODAY));
    }
  });

  it("원본의 개별 식별 값(이름·번호)이 들어 있지 않다", () => {
    const text = JSON.stringify(history);
    expect(/\b(IM|SD|C|HMD|SBA|SUB|WBS|PROD)\d{4,}\b/.test(text)).toBe(false);
  });
});

describe("assetClass (BPI 유형 대응)", () => {
  it("설비·IT 종류를 4가지로 묶는다", () => {
    expect(assetClass("HMI PC")).toBe("computer");
    expect(assetClass("방화벽")).toBe("network");
    expect(assetClass("공정 소프트웨어")).toBe("application");
    expect(assetClass("PLC")).toBe("device");
  });
});
