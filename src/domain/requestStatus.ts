import type { RequestStatus, Role } from "./types";

type Rule = { from: RequestStatus; to: RequestStatus; role: Role };

const RULES: Rule[] = [
  { from: "submitted", to: "approved", role: "admin" },
  { from: "submitted", to: "rejected", role: "admin" },
  { from: "submitted", to: "on_hold", role: "member" },
  { from: "approved", to: "in_progress", role: "member" },
  { from: "approved", to: "on_hold", role: "member" },
  { from: "in_progress", to: "done", role: "member" },
  { from: "in_progress", to: "on_hold", role: "member" },
  { from: "on_hold", to: "approved", role: "admin" },
  { from: "on_hold", to: "rejected", role: "admin" },
];

const ACTIVE: RequestStatus[] = ["submitted", "approved", "in_progress", "on_hold"];

export type TransitionInput = {
  from: RequestStatus;
  to: RequestStatus;
  role: Role;
  reason?: string;
  reviewDate?: string;
  resultNote?: string;
};

export type TransitionResult = { ok: true } | { ok: false; errors: string[] };

export function isActive(status: RequestStatus): boolean {
  return ACTIVE.includes(status);
}

function requiredFieldErrors(input: TransitionInput): string[] {
  const errors: string[] = [];
  const needsReason = input.to === "rejected" || input.to === "on_hold";
  if (needsReason && !input.reason?.trim()) errors.push("사유를 적어 주세요.");
  if (input.to === "on_hold" && !input.reviewDate) errors.push("재검토일을 골라 주세요.");
  if (input.to === "done" && !input.resultNote?.trim()) errors.push("처리 결과를 적어 주세요.");
  return errors;
}

export function validateTransition(input: TransitionInput): TransitionResult {
  const allowed = RULES.some(
    (rule) => rule.from === input.from && rule.to === input.to && rule.role === input.role,
  );
  if (!allowed) return { ok: false, errors: ["지금 상태에서는 할 수 없는 작업이에요."] };
  const errors = requiredFieldErrors(input);
  return errors.length === 0 ? { ok: true } : { ok: false, errors };
}

// 재검토일이 오늘이거나 지났으면 대시보드에 "재검토 필요"로 보인다.
export function isReviewDue(status: RequestStatus, reviewDate: string | undefined, today: string): boolean {
  return status === "on_hold" && !!reviewDate && reviewDate <= today;
}
