import type { PatchRequestView, RequestRepository, StatusHistoryRow } from "@/application/ports";
import { validateChecklist, type CompatibilityInput } from "@/domain/checklist";
import { isActive, validateTransition } from "@/domain/requestStatus";

// [C 소유] 요청 저장소의 가짜 구현(메모리). 규칙(domain)을 그대로 통과해야 한다. C가 Supabase 구현으로 바꾼다.
export function createFakeRequestRepository(): RequestRepository {
  const requests = new Map<string, PatchRequestView>();
  const history: StatusHistoryRow[] = [];
  let counter = 0;

  return {
    async create({ matchId, requesterId, checklist }) {
      const check = validateChecklist(checklist as CompatibilityInput);
      if (!check.ok) throw new Error(check.errors.join(" "));
      const duplicate = [...requests.values()].some((r) => r.matchId === matchId && isActive(r.status));
      if (duplicate) throw new Error("이미 진행 중인 요청이 있어요.");
      const request: PatchRequestView = {
        id: `fake-req-${++counter}`, matchId, requesterId, status: "submitted", actionType: "patch",
        createdAt: new Date().toISOString(),
      };
      requests.set(request.id, request);
      history.push({ requestId: request.id, toStatus: "submitted", actorId: requesterId, at: request.createdAt });
      return request;
    },

    async transition({ requestId, to, actor, reason, reviewDate, resultNote }) {
      const current = requests.get(requestId);
      if (!current) throw new Error("요청을 찾지 못했어요.");
      const result = validateTransition({ from: current.status, to, role: actor.role, reason, reviewDate, resultNote });
      if (!result.ok) throw new Error(result.errors.join(" "));
      const next = { ...current, status: to, reason, reviewDate, resultNote };
      requests.set(requestId, next);
      history.push({ requestId, fromStatus: current.status, toStatus: to, actorId: actor.id, at: new Date().toISOString(), reason });
      return next;
    },

    listForOwner: async (ownerId) => [...requests.values()].filter((r) => r.requesterId === ownerId),
    listAll: async (status) => [...requests.values()].filter((r) => !status || r.status === status),
    history: async (requestId) => history.filter((row) => row.requestId === requestId),
  };
}
