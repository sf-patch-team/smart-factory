/**
 * 개발용 시드: 가상 사용자·자산·KEV·매칭 후보·가상 이력을 Supabase에 넣는다.
 * 서비스 키(.env.local)로 접근 규칙(RLS)을 건너뛰므로 **프로젝트 소유자(A)만** 실행한다.
 * 사용: npx tsx scripts/seed.ts   (여러 번 실행해도 같은 결과가 되도록 만들었다)
 * 가상 사용자의 비밀번호는 .env.local의 SEED_USER_PASSWORD에 만들어 저장한다(값은 출력하지 않는다).
 */
import { createHash, randomBytes } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { computeScore } from "../src/domain/scoring";
import { findCandidates } from "../src/domain/matching";
import type { Asset, KevEntry } from "../src/domain/types";
import { parseKev } from "../src/infrastructure/kev/parseKev";
import { SEED_ASSETS } from "../src/infrastructure/seed/assets";
import { buildAssetHistory } from "../src/infrastructure/seed/assetHistory";

const ENV_PATH = path.resolve(import.meta.dirname, "../.env.local");
const KEV_URL = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json";
const BATCH = 400;

function loadEnv(): Record<string, string> {
  const env: Record<string, string> = {};
  for (const line of fs.readFileSync(ENV_PATH, "utf8").split(/\r?\n/)) {
    const match = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (match) env[match[1]] = match[2].trim();
  }
  return env;
}

const env = loadEnv();
const BASE = env.NEXT_PUBLIC_SUPABASE_URL;
const KEY = env.SUPABASE_SERVICE_ROLE_KEY;
if (!BASE || !KEY) throw new Error(".env.local에 Supabase 주소와 서비스 키가 필요해요.");

async function call(method: string, route: string, body?: unknown, prefer = "return=minimal") {
  const response = await fetch(`${BASE}${route}`, {
    method,
    headers: { apikey: KEY, Authorization: `Bearer ${KEY}`, "Content-Type": "application/json", Prefer: prefer },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`${method} ${route} → ${response.status} ${(await response.text()).slice(0, 300)}`);
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

const upsert = (table: string, rows: object[], conflict: string) =>
  call("POST", `/rest/v1/${table}?on_conflict=${conflict}`, rows, "resolution=merge-duplicates,return=minimal");

async function insertInBatches(table: string, rows: object[], conflict: string) {
  for (let i = 0; i < rows.length; i += BATCH) await upsert(table, rows.slice(i, i + BATCH), conflict);
}

// 같은 입력이면 같은 UUID가 나와서 다시 실행해도 중복이 생기지 않는다.
function uuidFrom(text: string): string {
  const hex = createHash("sha1").update(text).digest("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-5${hex.slice(13, 16)}-a${hex.slice(17, 20)}-${hex.slice(20, 32)}`;
}

function ensurePassword(): string {
  if (env.SEED_USER_PASSWORD) return env.SEED_USER_PASSWORD;
  const password = `Sf-${randomBytes(9).toString("base64url")}`;
  fs.appendFileSync(ENV_PATH, `\nSEED_USER_PASSWORD=${password}\n`);
  return password;
}

const USERS = [
  { email: "member1@example.com", name: "가상 담당자 1", role: "member" },
  { email: "member2@example.com", name: "가상 담당자 2", role: "member" },
  { email: "member3@example.com", name: "가상 담당자 3", role: "member" },
  { email: "admin@example.com", name: "가상 관리자", role: "admin" },
];

async function findUserId(email: string): Promise<string> {
  const list = await call("GET", "/auth/v1/admin/users?per_page=200");
  const found = (list.users as { id: string; email: string }[]).find((user) => user.email === email);
  if (!found) throw new Error(`사용자를 찾지 못했어요: ${email}`);
  return found.id;
}

async function ensureUsers(password: string): Promise<Record<string, string>> {
  const ids: Record<string, string> = {};
  for (const user of USERS) {
    try {
      const created = await call("POST", "/auth/v1/admin/users", {
        email: user.email, password, email_confirm: true, user_metadata: { display_name: user.name },
      });
      ids[user.email] = created.id;
    } catch {
      ids[user.email] = await findUserId(user.email); // 이미 있으면 그대로 쓴다
    }
    await call("PATCH", `/rest/v1/profiles?id=eq.${ids[user.email]}`, { role: user.role, display_name: user.name });
  }
  return ids;
}

function assetRow(asset: Asset, ownerId: string, index: number) {
  return {
    id: uuidFrom(asset.id), owner_id: ownerId, name: asset.name, vendor: asset.vendor, product: asset.product,
    version: asset.version, category: asset.category, asset_type: asset.assetType, zone: asset.zone, line: asset.line,
    criticality: asset.criticality, affected_equipment: asset.affectedEquipment, patch_constraints: asset.patchConstraints,
    rollback_possible: asset.rollbackPossible, is_active: true,
    last_verified_at: new Date(Date.now() - (index % 90) * 86_400_000).toISOString(), // 일부는 오래된 확인일
  };
}

async function seedAssets(owners: string[]) {
  const lines = [...new Set(SEED_ASSETS.map((asset) => asset.line))];
  const rows = SEED_ASSETS.map((asset, index) => assetRow(asset, owners[lines.indexOf(asset.line) % owners.length], index));
  await insertInBatches("assets", rows, "id");
  return rows.length;
}

async function loadKev(): Promise<KevEntry[]> {
  const response = await fetch(KEV_URL);
  if (!response.ok) throw new Error(`KEV를 받지 못했어요: ${response.status}`);
  const catalog = parseKev(await response.json());
  const [fetchRow] = await call("POST", "/rest/v1/kev_fetches", {
    trigger: "manual", finished_at: new Date().toISOString(), status: catalog.status,
    catalog_version: catalog.catalogVersion, entry_count: catalog.entries.length,
  }, "return=representation");
  const rows = catalog.entries.map((entry) => ({
    cve_id: entry.cveId, vendor_project: entry.vendorProject, product: entry.product,
    vulnerability_name: entry.vulnerabilityName, short_description: entry.shortDescription,
    required_action: entry.requiredAction, date_added: entry.dateAdded || null, due_date: entry.dueDate || null,
    ransomware_known: entry.ransomwareKnown, source_fetch_id: fetchRow.id, is_test: false,
  }));
  await insertInBatches("kev_entries", rows, "cve_id");
  return catalog.entries;
}

async function seedMatches(entries: KevEntry[], today: string) {
  const rows = SEED_ASSETS.flatMap((asset) =>
    findCandidates(asset, entries).map((entry) => {
      const score = computeScore(asset, entry, today);
      return {
        id: uuidFrom(`${asset.id}|${entry.cveId}`), asset_id: uuidFrom(asset.id), cve_id: entry.cveId,
        status: "candidate", score: score.total, score_breakdown: score.breakdown, scored_at: new Date().toISOString(),
      };
    }),
  );
  await insertInBatches("matches", rows, "asset_id,cve_id");
  return rows.length;
}

async function seedEvents(today: string) {
  const events = buildAssetHistory(SEED_ASSETS, today);
  await call("DELETE", "/rest/v1/asset_events?is_synthetic=eq.true");
  // 한 번에 넣는 행은 열 이름이 모두 같아야 해서, 해당 없는 열은 null로 채운다.
  const empty = {
    impact: null, resolved_after_days: null, handle_hours: null, reassignments: null, risk: null, emergency: null,
    cab_needed: null, planned_downtime_minutes: null, actual_duration_minutes: null, had_related_incident: null,
  };
  const rows = events.map((event) =>
    event.kind === "incident"
      ? { ...empty, asset_id: uuidFrom(event.assetId), kind: "incident", occurred_on: event.openedAt, impact: event.impact,
          resolved_after_days: event.resolvedAfterDays, handle_hours: event.handleHours, reassignments: event.reassignments }
      : { ...empty, asset_id: uuidFrom(event.assetId), kind: "change", occurred_on: event.startedAt, risk: event.risk,
          emergency: event.emergency, cab_needed: event.cabNeeded, planned_downtime_minutes: event.plannedDowntimeMinutes,
          actual_duration_minutes: event.actualDurationMinutes, had_related_incident: event.hadRelatedIncident },
  );
  for (let i = 0; i < rows.length; i += BATCH) await call("POST", "/rest/v1/asset_events", rows.slice(i, i + BATCH));
  return rows.length;
}

async function main() {
  const today = new Date().toISOString().slice(0, 10);
  const ids = await ensureUsers(ensurePassword());
  console.log("사용자", USERS.length, "명 준비(담당자 3 · 관리자 1)");
  const members = USERS.filter((user) => user.role === "member").map((user) => ids[user.email]);
  console.log("자산", await seedAssets(members), "개");
  const entries = await loadKev();
  console.log("KEV", entries.length, "개");
  console.log("매칭 후보", await seedMatches(entries, today), "건");
  console.log("가상 이력", await seedEvents(today), "건");
  await upsert("app_settings", [{ key: "test_mode", value: false }], "key");
}

main().catch((error) => {
  console.error("시드 실패:", error instanceof Error ? error.message : error);
  process.exit(1);
});
