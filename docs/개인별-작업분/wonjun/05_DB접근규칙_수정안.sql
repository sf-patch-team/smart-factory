-- DB 접근 규칙 수정안 (초안 — Supabase에 적용하지 않았다)
-- 목적: 담당자가 자기 요청의 상태를 직접 바꾸거나 삭제하지 못하게 하고,
--       상태 변경은 규칙·이력을 함께 처리하는 한 곳(서버 경로 또는 보안 함수)으로만 지나가게 한다.
-- 현재 문제: requests_own(FOR ALL, requester_id = auth.uid())가 모든 열의 수정·삭제를 허용한다.

-- 1) patch_requests: 담당자는 읽기와 신청(INSERT)만 한다.
drop policy if exists requests_own on patch_requests;
drop policy if exists requests_admin_decide on patch_requests;

create policy requests_member_read on patch_requests
  for select using (requester_id = auth.uid());

create policy requests_member_submit on patch_requests
  for insert with check (requester_id = auth.uid() and status = 'submitted');

-- 관리자의 읽기 정책(requests_admin_read)은 유지한다.
-- 승인·반려·처리·완료 등 모든 상태 변경은 서버(서비스 키) 또는 아래 보안 함수만 한다.
-- (request_status_history에는 쓰기 정책이 없으므로 이력 기록도 서버 경로로만 가능하다.)

-- 2) 상태 전이 보안 함수 — 별도 설계 필요(규칙 요약)
--    입력: 요청 ID, 새 상태, 사유, 재검토일, 처리 결과, 작업 키(재전송 중복 방지)
--    처리: 호출자 역할 확인 → domain/requestStatus.ts와 같은 허용 전이·필수 항목 검사
--          → 요청 상태 갱신 + request_status_history 한 행을 한 번에 기록(둘 중 하나라도 실패하면 모두 취소)
--    금지: 요청자와 같은 사용자의 승인·완료 수락, 허용되지 않은 전이

-- 3) matches: 담당자는 확인 관련 열만 바꾼다(점수·후보 식별 열 변경 금지).
revoke update on matches from authenticated;
grant update (status, note, decided_by, decided_at) on matches to authenticated;

-- 4) 적용 뒤 확인할 시험 (모두 거부되어야 한다)
--    a. member 로그인 키로 자기 요청의 status를 'done'으로 PATCH      → 거부
--    b. member 로그인 키로 자기 요청 삭제(DELETE)                       → 거부
--    c. member가 status='done'으로 신규 요청 INSERT                      → 거부
--    d. member가 matches.score 또는 asset_id를 PATCH                     → 거부
--    e. member가 타인의 요청·후보·이력 조회                              → 0건
--    f. member가 status='submitted'로 자기 요청 신청                     → 허용
