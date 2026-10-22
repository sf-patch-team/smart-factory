export type Category = "OT" | "IT";
export type Criticality = "high" | "mid" | "low";
export type MatchStatus = "candidate" | "confirmed" | "dismissed";
export type Role = "member" | "admin";

export type RequestStatus =
  | "submitted"
  | "approved"
  | "rejected"
  | "in_progress"
  | "done"
  | "on_hold";

export type Asset = {
  id: string;
  name: string;
  vendor: string;
  product: string;
  version: string;
  category: Category;
  assetType: string; // 예: HMI PC, PLC, 산업용 스위치, 방화벽
  zone: string; // 구역 (예: 조립동)
  line: string; // 라인 (예: 조립 라인 1)
  criticality: Criticality;
  affectedEquipment: string;
  patchConstraints: string[];
  rollbackPossible: boolean;
};

export type KevEntry = {
  cveId: string;
  vendorProject: string;
  product: string;
  vulnerabilityName: string;
  dateAdded: string; // YYYY-MM-DD
  dueDate: string; // YYYY-MM-DD
  ransomwareKnown: boolean;
  shortDescription: string;
  requiredAction: string;
};
