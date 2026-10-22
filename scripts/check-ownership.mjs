// 내가 바꾼 파일이 내 영역 안에 있는지 검사한다(영역은 scripts/ownership.json).
// 사용: npm run check:owner -- a        (a·b·c 중 내 역할. 기준은 origin/main 대비 변경 파일)
// 공유 파일(shared)과 남의 영역을 고치면 알려 주고, 남의 영역이면 실패(종료 코드 1)로 끝낸다.
import { execSync } from "node:child_process";
import fs from "node:fs";

const role = process.argv[2];
const config = JSON.parse(fs.readFileSync(new URL("./ownership.json", import.meta.url), "utf8"));
if (!config.owners[role]) {
  console.error("사용법: npm run check:owner -- a|b|c");
  process.exit(2);
}

const base = process.argv[3] ?? "origin/main";
const changed = execSync(`git diff --name-only ${base}...HEAD`, { encoding: "utf8" })
  .split("\n").map((line) => line.trim()).filter(Boolean);

const startsWithAny = (file, prefixes) => prefixes.some((prefix) => file.startsWith(prefix));
const ownerOf = (file) => Object.keys(config.owners).find((name) => startsWithAny(file, config.owners[name]));

const foreign = [];
const shared = [];
// 작업 로그는 사람별 파일(<날짜>-a.md)이다. 공통 로그(<날짜>.md)는 A만 고친다.
function logOwner(file) {
  const match = file.match(/^docs\/작업로그\/\d{4}-\d{2}-\d{2}(?:-([abc]))?\.md$/);
  return match ? (match[1] ?? "a") : null;
}

for (const file of changed) {
  const logger = logOwner(file);
  if (logger) {
    if (logger !== role) foreign.push(`${file}  (소유: ${logger.toUpperCase()})`);
    continue;
  }
  if (startsWithAny(file, config.anyone)) continue;
  if (startsWithAny(file, config.shared)) { shared.push(file); continue; }
  const owner = ownerOf(file);
  if (owner && owner !== role) foreign.push(`${file}  (소유: ${owner.toUpperCase()})`);
  if (!owner) foreign.push(`${file}  (소유자 없음 — scripts/ownership.json에 먼저 추가)`);
}

console.log(`변경 파일 ${changed.length}개 · 내 역할 ${role.toUpperCase()}`);
if (shared.length) console.log(`\n⚠ 공유 파일 — 제공자와 사용자 둘 다 리뷰가 필요해요:\n  ${shared.join("\n  ")}`);
if (foreign.length) {
  console.log(`\n✗ 남의 영역이거나 소유자가 없는 파일:\n  ${foreign.join("\n  ")}`);
  console.log("\n→ 그 사람에게 요청하거나, 합의한 뒤 작은 PR로 따로 올려 주세요.");
  process.exit(1);
}
console.log("\n✓ 내 영역 안에서만 바꿨어요.");
