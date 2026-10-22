import { describe, expect, it } from "vitest";
import type { CurrentUser } from "@/application/ports";
import { createFakeRequestRepository } from "@/infrastructure/container/requests";

const member: CurrentUser = { id: "m1", role: "member", displayName: "담당자" };
const admin: CurrentUser = { id: "ad", role: "admin", displayName: "관리자" };
const checklist = { vendorSupport: "yes", tested: "yes", rollbackPlan: "복원", downtimeImpact: "5분" };

describe("가짜 요청 저장소: 계약대로 동작한다 (S-08, S-09, S-10)", () => {
  it("신청 → 승인 → 처리 중 → 완료까지 가고 상태 이력이 4건 남는다", async () => {
    const repo = createFakeRequestRepository();
    const request = await repo.create({ matchId: "m", requesterId: member.id, checklist });
    await repo.transition({ requestId: request.id, to: "approved", actor: admin });
    await repo.transition({ requestId: request.id, to: "in_progress", actor: member });
    const done = await repo.transition({ requestId: request.id, to: "done", actor: member, resultNote: "패치 적용" });
    expect(done.status).toBe("done");
    expect(await repo.history(request.id)).toHaveLength(4);
  });

  it("체크리스트가 비면 신청되지 않고, 같은 항목을 다시 신청하면 막힌다", async () => {
    const repo = createFakeRequestRepository();
    await expect(repo.create({ matchId: "m", requesterId: member.id, checklist: {} })).rejects.toThrow();
    await repo.create({ matchId: "m", requesterId: member.id, checklist });
    await expect(repo.create({ matchId: "m", requesterId: member.id, checklist })).rejects.toThrow("진행 중");
  });

  it("담당자는 승인할 수 없고, 반려는 사유가 있어야 한다", async () => {
    const repo = createFakeRequestRepository();
    const request = await repo.create({ matchId: "m", requesterId: member.id, checklist });
    await expect(repo.transition({ requestId: request.id, to: "approved", actor: member })).rejects.toThrow();
    await expect(repo.transition({ requestId: request.id, to: "rejected", actor: admin })).rejects.toThrow("사유");
  });
});
