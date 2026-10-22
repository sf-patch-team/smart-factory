import { describe, expect, it } from "vitest";
import { createFakeKevRepository } from "@/infrastructure/container/kev";
import { createFakeMatchRepository } from "@/infrastructure/container/matches";
import { createFakeAssetRepository } from "@/infrastructure/container/assets";
import { TEST_KEV_ENTRIES } from "@/infrastructure/seed/testKev";

const okFetch = { trigger: "manual", finishedAt: "2026-10-22T00:00:00Z", status: "ok", catalogVersion: "v", entryCount: 1 } as const;

describe("가짜 KEV 저장소 (S-04, S-05)", () => {
  it("가져오기가 실패하면 이전 데이터를 유지하고 실패 상태를 기록한다", async () => {
    const repo = createFakeKevRepository();
    const before = (await repo.list()).length;
    await repo.replaceAll([], { ...okFetch, status: "failed", errorMessage: "연결 실패" });
    expect((await repo.list()).length).toBe(before);
    expect((await repo.lastFetch())?.status).toBe("failed");
  });

  it("성공하면 새 데이터로 바뀌고 받은 시각이 남는다", async () => {
    const repo = createFakeKevRepository();
    await repo.replaceAll(TEST_KEV_ENTRIES.slice(0, 2), okFetch);
    expect(await repo.list()).toHaveLength(2);
    expect((await repo.lastFetch())?.finishedAt).toBe(okFetch.finishedAt);
  });
});

describe("가짜 매칭 저장소 (S-06, S-07)", () => {
  it("후보가 만들어지고 확인하면 상태가 바뀐다", async () => {
    const assets = createFakeAssetRepository();
    const matches = createFakeMatchRepository(() => assets.listAll(), createFakeKevRepository());
    const candidates = await matches.listAll("candidate");
    expect(candidates.length).toBeGreaterThan(0);
    const first = candidates[0];
    await matches.decide(first.matchId, "confirmed", "해당함", "m1");
    expect((await matches.listAll("confirmed")).map((row) => row.matchId)).toContain(first.matchId);
    expect((await matches.listAll("candidate")).map((row) => row.matchId)).not.toContain(first.matchId);
  });
});
