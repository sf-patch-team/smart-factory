import type { FetchRecord, KevRepository } from "@/application/ports";
import type { KevEntry } from "@/domain/types";
import { TEST_KEV_ENTRIES } from "@/infrastructure/seed/testKev";

// [B 소유] KEV 저장소의 가짜 구현(시험용 KEV 12개). B가 Supabase 구현으로 바꾼다.
export function createFakeKevRepository(initial: KevEntry[] = TEST_KEV_ENTRIES): KevRepository {
  let entries = initial;
  let last: FetchRecord | null = {
    trigger: "test", finishedAt: new Date().toISOString(), status: "ok", catalogVersion: "test", entryCount: initial.length,
  };
  return {
    // 실패하면 이전 데이터를 유지한다(R-05).
    replaceAll: async (next, fetch) => {
      if (fetch.status === "failed") { last = fetch; return; }
      entries = next;
      last = fetch;
    },
    list: async () => entries,
    lastFetch: async () => last,
  };
}
