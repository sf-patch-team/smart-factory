import { StatusChip } from "./StatusChip";

export type DataState = "read" | "empty" | "failed";

const STATE_VIEW = {
  read: { label: "읽음", tone: "ok" },
  empty: { label: "내용 없음", tone: "neutral" },
  failed: { label: "못 읽음", tone: "danger" },
} as const;

type Props = { state: DataState; receivedAt?: string; testMode?: boolean };

// FR-06: 모든 위험 화면에 받은 시각과 데이터 상태를 보여 준다.
export function DataStatusBar({ state, receivedAt, testMode }: Props) {
  const view = STATE_VIEW[state];
  return (
    <div className="status-bar" role="status">
      <span>KEV 데이터</span>
      <StatusChip label={view.label} tone={view.tone} />
      <span>{receivedAt ? `받은 시각 ${receivedAt}` : "아직 받아온 적이 없어요"}</span>
      {testMode && <StatusChip label="시험 모드" tone="warn" />}
    </div>
  );
}
