-- 자산 과거 이력(장애·변경) 표. R-26(Could), spec Q-08.
-- 2026-10-22 사용자 승인 후 Supabase 프로젝트 smart-factory에 적용했다.
-- 데이터는 BPI 2013·2014 통계로 만든 가상 이력이다(docs/data-sources.md). 쓰기는 서버(서비스 키)만 한다.

create table asset_events (
  id bigint generated always as identity primary key,
  asset_id uuid not null references assets (id),
  kind text not null check (kind in ('incident', 'change')),
  occurred_on date not null,
  -- 장애
  impact text check (impact in ('high', 'medium', 'low')),
  resolved_after_days numeric,
  handle_hours numeric,
  reassignments int,
  -- 변경
  risk text check (risk in ('minor', 'business', 'major')),
  emergency boolean,
  cab_needed boolean,
  planned_downtime_minutes int,
  actual_duration_minutes int,
  had_related_incident boolean,
  is_synthetic boolean not null default true
);

create index asset_events_asset_idx on asset_events (asset_id, occurred_on desc);

alter table asset_events enable row level security;

create policy asset_events_read on asset_events for select using (
  is_admin() or exists (select 1 from assets a where a.id = asset_id and a.owner_id = auth.uid())
);
