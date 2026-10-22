// 자산의 과거 이력(장애·변경). 가상 데이터이며 출처와 가정은 docs/data-sources.md.
export type EventImpact = "high" | "medium" | "low";
export type ChangeRisk = "minor" | "business" | "major";

export type IncidentEvent = {
  kind: "incident";
  assetId: string;
  openedAt: string; // YYYY-MM-DD
  resolvedAfterDays: number;
  handleHours: number;
  reassignments: number;
  impact: EventImpact;
};

export type ChangeEvent = {
  kind: "change";
  assetId: string;
  startedAt: string;
  risk: ChangeRisk;
  emergency: boolean;
  cabNeeded: boolean;
  plannedDowntimeMinutes: number; // 0이면 계획된 중단 없음
  actualDurationMinutes: number;
  hadRelatedIncident: boolean; // 연결된 장애가 있었다는 뜻이며 원인이라는 뜻은 아니다
};

export type AssetEvent = IncidentEvent | ChangeEvent;
