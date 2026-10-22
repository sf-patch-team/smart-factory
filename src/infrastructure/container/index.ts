import { createFakeAssetRepository } from "./assets";
import { createFakeAuditLog, createFakeCurrentUser } from "./auth";
import { createFakeKevRepository } from "./kev";
import { createFakeMatchRepository } from "./matches";
import { createFakeRequestRepository } from "./requests";

// [A 소유] 조립 지점. 각자 자기 파일의 구현을 가짜에서 Supabase 구현으로 바꾸면 여기는 거의 안 바뀐다.
// 각 영역은 계약(application/ports.ts)만 보고 일하므로, 다른 사람 구현이 끝나기를 기다리지 않아도 된다.
export function createContainer() {
  const currentUser = createFakeCurrentUser();
  const audit = createFakeAuditLog();
  const assets = createFakeAssetRepository();
  const kev = createFakeKevRepository();
  const matches = createFakeMatchRepository(() => assets.listAll(), kev);
  const requests = createFakeRequestRepository();
  return { currentUser, audit, assets, kev, matches, requests };
}

export type Container = ReturnType<typeof createContainer>;
