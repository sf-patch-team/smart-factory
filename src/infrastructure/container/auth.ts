import type { AuditLog, CurrentUser, CurrentUserProvider } from "@/application/ports";

// [A 소유] 로그인 연결 전까지 쓰는 가짜 사용자와 가짜 활동 기록. A가 Supabase 구현으로 바꾼다.
const FAKE_USERS: Record<"member" | "admin", CurrentUser> = {
  member: { id: "fake-member", role: "member", displayName: "가상 담당자" },
  admin: { id: "fake-admin", role: "admin", displayName: "가상 관리자" },
};

export function createFakeCurrentUser(role: "member" | "admin" = "member"): CurrentUserProvider {
  return { get: async () => FAKE_USERS[role] };
}

export function createFakeAuditLog(): AuditLog & { entries: object[] } {
  const entries: object[] = [];
  return { entries, record: async (entry) => void entries.push({ ...entry, at: new Date().toISOString() }) };
}
