import { describe, expect, it } from "vitest";
import { computeScore } from "@/domain/scoring";
import { findCandidates, isCandidate } from "@/domain/matching";
import { validateChecklist } from "@/domain/checklist";
import { isActive, isReviewDue, validateTransition } from "@/domain/requestStatus";
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

describe("checklist (R-11, R-12, S-09, ADR 0002)", () => {
  it("필수 항목이 비어 있으면 오류 4개를 낸다", () => {
    const result = validateChecklist({});
    expect(result.ok).toBe(false);
    expect(result.errors).toHaveLength(4);
  });

  it("모두 채우면 통과한다", () => {
    const result = validateChecklist({
      vendorSupport: "yes", tested: "yes", rollbackPlan: "이전 버전으로 복원", downtimeImpact: "5분 정지",
    });
    expect(result.ok).toBe(true);
    expect(result.suggestHoldOrMitigation).toBe(false);
  });

  it("벤더 지원이 아니오/모름이면 완화 조치·보류를 안내하되 막지는 않는다", () => {
    const result = validateChecklist({
      vendorSupport: "unknown", tested: "no", rollbackPlan: "복원", downtimeImpact: "없음",
    });
    expect(result.ok).toBe(true);
    expect(result.suggestHoldOrMitigation).toBe(true);
  });
});

describe("requestStatus (R-12, R-15~17, S-08, S-10, S-11)", () => {
  it("관리자만 신청을 승인할 수 있다", () => {
    expect(validateTransition({ from: "submitted", to: "approved", role: "admin" }).ok).toBe(true);
    expect(validateTransition({ from: "submitted", to: "approved", role: "member" }).ok).toBe(false);
  });

  it("반려는 사유가 없으면 안 된다", () => {
    expect(validateTransition({ from: "submitted", to: "rejected", role: "admin" }).ok).toBe(false);
    expect(validateTransition({ from: "submitted", to: "rejected", role: "admin", reason: "근거 부족" }).ok).toBe(true);
  });

  it("보류는 사유와 재검토일이 모두 있어야 한다", () => {
    const base = { from: "approved", to: "on_hold", role: "member" } as const;
    expect(validateTransition({ ...base, reason: "벤더 미지원" }).ok).toBe(false);
    expect(validateTransition({ ...base, reviewDate: "2026-11-15" }).ok).toBe(false);
    expect(validateTransition({ ...base, reason: "벤더 미지원", reviewDate: "2026-11-15" }).ok).toBe(true);
  });

  it("처리 결과가 없으면 완료할 수 없다", () => {
    expect(validateTransition({ from: "in_progress", to: "done", role: "member" }).ok).toBe(false);
    expect(validateTransition({ from: "in_progress", to: "done", role: "member", resultNote: "패치 적용" }).ok).toBe(true);
  });

  it("허용되지 않은 건너뛰기는 거절한다", () => {
    expect(validateTransition({ from: "submitted", to: "done", role: "member", resultNote: "x" }).ok).toBe(false);
    expect(validateTransition({ from: "done", to: "approved", role: "admin" }).ok).toBe(false);
  });

  it("진행 중인 상태만 중복 신청을 막는 대상이다", () => {
    expect(isActive("submitted")).toBe(true);
    expect(isActive("on_hold")).toBe(true);
    expect(isActive("done")).toBe(false);
    expect(isActive("rejected")).toBe(false);
  });

  it("재검토일이 지난 보류만 '재검토 필요'가 된다", () => {
    expect(isReviewDue("on_hold", "2026-10-20", TODAY)).toBe(true);
    expect(isReviewDue("on_hold", "2026-11-01", TODAY)).toBe(false);
    expect(isReviewDue("approved", "2026-10-20", TODAY)).toBe(false);
  });
});

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
