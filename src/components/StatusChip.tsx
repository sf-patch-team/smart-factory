import type { RequestStatus } from "@/domain/types";

type Tone = "neutral" | "ok" | "warn" | "danger" | "info";

// docs/design.md 5절: 상태는 점 + 글자로 표시하고 색만으로 구분하지 않는다.
const REQUEST_STATUS: Record<RequestStatus, { label: string; tone: Tone }> = {
  submitted: { label: "신청", tone: "neutral" },
  approved: { label: "승인", tone: "info" },
  in_progress: { label: "처리 중", tone: "warn" },
  done: { label: "완료", tone: "ok" },
  rejected: { label: "반려", tone: "danger" },
  on_hold: { label: "‖ 보류", tone: "neutral" },
};

export function StatusChip({ label, tone }: { label: string; tone: Tone }) {
  return <span className={`chip ${tone === "neutral" ? "" : tone}`}>{label}</span>;
}

export function RequestStatusChip({ status }: { status: RequestStatus }) {
  const { label, tone } = REQUEST_STATUS[status];
  return <StatusChip label={label} tone={tone} />;
}
