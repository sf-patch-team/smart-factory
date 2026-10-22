export type VendorSupport = "yes" | "no" | "unknown";
export type Tested = "yes" | "no" | "na";

export type CompatibilityInput = {
  vendorSupport?: VendorSupport;
  tested?: Tested;
  rollbackPlan?: string;
  downtimeImpact?: string;
};

export type ChecklistResult = {
  ok: boolean;
  errors: string[];
  // 앱은 호환 여부를 판정하지 않는다(ADR 0002). 사람이 "아니오/모름"이라 답한 경우만 안내한다.
  suggestHoldOrMitigation: boolean;
};

export function validateChecklist(input: CompatibilityInput): ChecklistResult {
  const errors: string[] = [];
  if (!input.vendorSupport) errors.push("벤더가 이 패치를 지원하는지 골라 주세요.");
  if (!input.tested) errors.push("시험 결과를 골라 주세요.");
  if (!input.rollbackPlan?.trim()) errors.push("되돌리기 계획을 적어 주세요.");
  if (!input.downtimeImpact?.trim()) errors.push("가동에 미치는 영향을 적어 주세요.");
  const doubtful = input.vendorSupport === "no" || input.vendorSupport === "unknown";
  return { ok: errors.length === 0, errors, suggestHoldOrMitigation: doubtful };
}
