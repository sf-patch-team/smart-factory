import type { AssetEvent } from "@/domain/history";
import type { ScoreBreakdown } from "@/domain/scoring";
import type { Asset, KevEntry, MatchStatus, RequestStatus, Role } from "@/domain/types";

// 3명이 동시에 개발하도록 먼저 약속해 두는 "계약"이다(docs/팀-작업계획.md 2절).
// 구현하는 사람이 정해져 있다. 계약을 바꿀 때는 이 파일만 작은 PR로 먼저 올리고 알린다.

export type CurrentUser = { id: string; role: Role; displayName: string };

export type FetchStatus = "ok" | "empty" | "failed";

export type FetchRecord = {
  trigger: "cron" | "manual" | "test";
  finishedAt: string; // ISO 시각 = 화면의 "받은 시각"
  status: FetchStatus;
  catalogVersion: string;
  entryCount: number;
  errorMessage?: string;
};

export type RiskView = {
  matchId: string;
  asset: Asset;
  entry: KevEntry;
  status: MatchStatus;
  score: number;
  scoreBreakdown: ScoreBreakdown;
  note?: string;
};

export type PatchRequestView = {
  id: string;
  matchId: string;
  requesterId: string;
  status: RequestStatus;
  actionType: "patch" | "mitigation";
  reason?: string;
  reviewDate?: string;
  resultNote?: string;
  createdAt: string;
};

export type StatusHistoryRow = {
  requestId: string;
  fromStatus?: RequestStatus;
  toStatus: RequestStatus;
  actorId: string;
  at: string;
  reason?: string;
};

// [A 구현] 로그인 사용자와 감사 기록
export interface CurrentUserProvider {
  get(): Promise<CurrentUser | null>;
}
export interface AuditLog {
  record(entry: { actorId?: string; action: string; entityType: string; entityId?: string; detail?: object }): Promise<void>;
}

// [C 구현] 자산
export interface AssetRepository {
  listForOwner(ownerId: string): Promise<Asset[]>;
  listAll(): Promise<Asset[]>; // 관리자용
  save(asset: Asset, actorId: string): Promise<Asset>; // 변경 이력(asset_changes)도 함께 남긴다
}

// [B 구현] KEV 저장과 매칭
export interface KevRepository {
  replaceAll(entries: KevEntry[], fetch: FetchRecord): Promise<void>; // 실패 시 이전 데이터를 유지한다
  list(): Promise<KevEntry[]>;
  lastFetch(): Promise<FetchRecord | null>;
}
export interface MatchRepository {
  upsertCandidates(): Promise<number>; // 자산 × KEV 후보 생성, 만든 개수 반환
  listForOwner(ownerId: string, status?: MatchStatus): Promise<RiskView[]>;
  listAll(status?: MatchStatus): Promise<RiskView[]>;
  decide(matchId: string, status: "confirmed" | "dismissed", note: string, actorId: string): Promise<void>;
}

// [C 구현] 패치 요청과 상태 이력
export interface RequestRepository {
  create(input: { matchId: string; requesterId: string; checklist: object }): Promise<PatchRequestView>;
  transition(input: {
    requestId: string; to: RequestStatus; actor: CurrentUser;
    reason?: string; reviewDate?: string; resultNote?: string;
  }): Promise<PatchRequestView>; // 규칙(domain/requestStatus)을 통과해야 하고, 이력 1행을 남긴다
  listForOwner(ownerId: string): Promise<PatchRequestView[]>;
  listAll(status?: RequestStatus): Promise<PatchRequestView[]>;
  history(requestId: string): Promise<StatusHistoryRow[]>;
}

// [C 구현, Could] 자산 과거 이력(R-26). DB 표 승인 전에는 seed/assetHistory.ts로 대신한다.
export interface AssetEventRepository {
  listForAsset(assetId: string): Promise<AssetEvent[]>;
}
