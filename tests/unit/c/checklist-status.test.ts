import { describe, expect, it } from "vitest";
import { validateChecklist } from "@/domain/checklist";
import { isActive, isReviewDue, validateTransition } from "@/domain/requestStatus";

const TODAY = "2026-10-22";

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
