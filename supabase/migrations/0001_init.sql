-- smart-factory 초기 표 (docs/db/erd.md 2~5절).
-- 2026-10-22 사용자가 본인 Supabase 계정 사용을 승인해 새 프로젝트 smart-factory에 적용한다.

create table profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null,
  role text not null default 'member' check (role in ('member', 'admin')),
  created_at timestamptz not null default now()
);

-- 관리자 판정은 RLS에서 profiles를 다시 읽으므로 보안 함수로 한 번만 만든다.
create function is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from profiles where id = auth.uid() and role = 'admin');
$$;

-- 가입하면 담당자 프로필을 만든다(R-01). 관리자는 DB에서 직접 지정한다.
create function handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)));
  return new;
end;
$$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function handle_new_user();

create table assets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references profiles (id),
  name text not null,
  vendor text not null,
  product text not null,
  version text not null default '',
  category text not null check (category in ('OT', 'IT')),
  asset_type text not null default '',
  zone text not null default '',
  line text not null default '',
  criticality text not null check (criticality in ('high', 'mid', 'low')),
  affected_equipment text not null default '',
  patch_constraints text[] not null default '{}',
  rollback_possible boolean not null default false,
  last_verified_at timestamptz,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table asset_changes (
  id bigint generated always as identity primary key,
  asset_id uuid not null references assets (id),
  changed_by uuid not null references profiles (id),
  changed_at timestamptz not null default now(),
  before jsonb,
  after jsonb
);

create table kev_fetches (
  id bigint generated always as identity primary key,
  trigger text not null check (trigger in ('cron', 'manual', 'test')),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null check (status in ('ok', 'empty', 'failed')),
  catalog_version text,
  entry_count int not null default 0,
  error_message text
);

create table kev_entries (
  cve_id text primary key,
  vendor_project text not null,
  product text not null,
  vulnerability_name text not null default '',
  short_description text not null default '',
  required_action text not null default '',
  date_added date,
  due_date date,
  ransomware_known boolean not null default false,
  notes text,
  cwes text[] not null default '{}',
  source_fetch_id bigint references kev_fetches (id),
  is_test boolean not null default false
);

create table matches (
  id uuid primary key default gen_random_uuid(),
  asset_id uuid not null references assets (id),
  cve_id text not null references kev_entries (cve_id),
  status text not null default 'candidate' check (status in ('candidate', 'confirmed', 'dismissed')),
  decided_by uuid references profiles (id),
  decided_at timestamptz,
  note text,
  score int not null default 0,
  score_breakdown jsonb not null default '{}',
  scored_at timestamptz,
  unique (asset_id, cve_id)
);

create table patch_requests (
  id uuid primary key default gen_random_uuid(),
  match_id uuid not null references matches (id),
  requester_id uuid not null references profiles (id),
  status text not null default 'submitted'
    check (status in ('submitted', 'approved', 'rejected', 'in_progress', 'done', 'on_hold')),
  action_type text not null default 'patch' check (action_type in ('patch', 'mitigation')),
  vendor_support text check (vendor_support in ('yes', 'no', 'unknown')),
  tested text check (tested in ('yes', 'no', 'na')),
  rollback_plan text,
  downtime_impact text,
  planned_date date,
  review_date date,
  reason text,
  result_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

-- 같은 위험 항목에는 진행 중인 요청을 1건만 둔다(Ex-04).
create unique index one_active_request_per_match on patch_requests (match_id)
  where status in ('submitted', 'approved', 'in_progress', 'on_hold');

create table request_status_history (
  id bigint generated always as identity primary key,
  request_id uuid not null references patch_requests (id),
  from_status text,
  to_status text not null,
  actor_id uuid not null references profiles (id),
  at timestamptz not null default now(),
  reason text
);

create table audit_log (
  id bigint generated always as identity primary key,
  actor_id uuid references profiles (id),
  action text not null,
  entity_type text not null,
  entity_id text,
  detail jsonb not null default '{}',
  at timestamptz not null default now()
);

create table app_settings (
  key text primary key,
  value jsonb not null
);

-- 행 수준 보안(docs/db/erd.md 3절). 외부 데이터 쓰기는 서버의 서비스 키만 한다.
alter table profiles enable row level security;
alter table assets enable row level security;
alter table asset_changes enable row level security;
alter table kev_fetches enable row level security;
alter table kev_entries enable row level security;
alter table matches enable row level security;
alter table patch_requests enable row level security;
alter table request_status_history enable row level security;
alter table audit_log enable row level security;
alter table app_settings enable row level security;

create policy profiles_read on profiles for select using (id = auth.uid() or is_admin());

create policy assets_own on assets for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy assets_admin_read on assets for select using (is_admin());

create policy asset_changes_read on asset_changes for select using (
  is_admin() or exists (select 1 from assets a where a.id = asset_id and a.owner_id = auth.uid())
);

create policy kev_fetches_read on kev_fetches for select using (auth.uid() is not null);
create policy kev_entries_read on kev_entries for select using (auth.uid() is not null);
create policy app_settings_read on app_settings for select using (auth.uid() is not null);

create policy matches_read on matches for select using (
  is_admin() or exists (select 1 from assets a where a.id = asset_id and a.owner_id = auth.uid())
);
create policy matches_decide on matches for update using (
  exists (select 1 from assets a where a.id = asset_id and a.owner_id = auth.uid())
);

create policy requests_own on patch_requests for all
  using (requester_id = auth.uid()) with check (requester_id = auth.uid());
create policy requests_admin_read on patch_requests for select using (is_admin());
create policy requests_admin_decide on patch_requests for update using (is_admin());

create policy history_read on request_status_history for select using (
  is_admin() or exists (select 1 from patch_requests r where r.id = request_id and r.requester_id = auth.uid())
);

create policy audit_admin_read on audit_log for select using (is_admin());

-- 보안 함수는 API로 직접 부르지 못하게 한다(로그인하지 않은 사용자 포함).
revoke execute on function is_admin() from public, anon;
grant execute on function is_admin() to authenticated;
revoke execute on function handle_new_user() from public, anon, authenticated;
