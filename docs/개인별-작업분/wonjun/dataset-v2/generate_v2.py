"""가상 공장 데이터셋 v2 생성기. 원본 JSON은 고치지 않고 파생 파일을 만든다(고정 난수 → 재현 가능).

사용: python -X utf8 -I generate_v2.py <원본 폴더> <출력 폴더> [research_versions.json]
원본의 AI4I 관측값(original 객체)은 한 글자도 바꾸지 않는다. 값은 모두 시험용 가정이며 실제 회사 자료가 아니다.
"""
import collections
import copy
import datetime as dt
import json
import math
import pathlib
import random
import re
import sys

import v2_rules as R


def weighted(rng, options):
    x, acc = rng.random(), 0.0
    for p, value in options:
        acc += p
        if x < acc:
            return value
    return options[-1][1]


# ---------- 자산 속성 ----------
def vary_attributes(assets, rng):
    for a in assets:
        t, changed = a["assetType"], []
        for key, table in (("criticality", R.CRITICALITY), ("lifecycle", R.LIFECYCLE)):
            if t in table:
                new = weighted(rng, table[t])
                if new != a[key]:
                    a[key] = new; changed.append(key)
        if rng.random() < R.ROLLBACK_TRUE_CHANCE.get(t, 0):
            a["rollbackPossible"] = True; changed.append("rollbackPossible")
        if rng.random() < R.ROLLBACK_FALSE_CHANCE.get(t, 0):
            a["rollbackPossible"] = False; changed.append("rollbackPossible")
        cons = list(a["patchConstraints"])
        for typ, token, p in sorted(R.EXTRA_CONSTRAINT):
            if typ == t and token not in cons and rng.random() < p:
                cons.append(token)
        if rng.random() < R.CLEAR_CONSTRAINT_CHANCE.get(t, 0):
            cons = []
        if cons != a["patchConstraints"]:
            a["patchConstraints"] = cons; changed.append("patchConstraints")
        if changed:
            a["variationV2"] = sorted(set(changed))
            a["provenanceV2"] = "synthetic_variation_v2"


NO_EDR = {"코어 스위치", "방화벽", "가상화 호스트", "산업용 스위치", "PLC", "CNC 컨트롤러", "로봇 컨트롤러", "인버터", "바코드 리더"}


def add_exposure_edr_reboot(assets, lines, rng):
    line_window = {l["id"]: rng.choice(R.REBOOT_OT) for l in lines}
    for a in assets:
        t = a["assetType"]
        a["exposure"] = R.EXPOSURE.get(t) or ("remote" if t == "엔지니어링 PC" and rng.random() < R.REMOTE_ENGINEERING_CHANCE else "internal")
        a["edr"] = None if t in NO_EDR else rng.random() < R.EDR_CHANCE.get(t, 0.75)
        ot_window = line_window.get(a["line"])
        a["rebootWindow"] = ot_window if (a["category"] == "OT" and ot_window) else rng.choice(R.REBOOT_IT)
        a["fieldsV2Provenance"] = "synthetic_assumption(exposure, edr, rebootWindow)"


# ---------- 이질성 ----------
def apply_heterogeneity(d, rng):
    spec = R.HETERO[d["code"]]
    bad = {i["rowId"].replace("-DUP", "") for i in d["quality_truth"]["issues"] if i["field"] in ("제조사", "제품", "버전")}
    row_by_asset = {}
    for rid, aid in d["quality_truth"]["row_to_asset"].items():
        row_by_asset.setdefault(aid, []).append(rid)
    cand = [a for a in d["canonical_assets"] if a["assetType"] == spec["assetType"]
            and not any(r.replace("-DUP", "") in bad for r in row_by_asset.get(a["id"], []))]
    chosen = rng.sample(cand, min(spec["count"], len(cand)))
    raw = {r["id"]: r for r in d["raw_asset_register"]}
    for a in chosen:
        old = (a["vendor"], a["product"], a["version"])
        a["vendor"], a["product"], a["version"] = spec["vendor"], spec["product"], spec["version"]
        a["heterogeneityV2"] = spec["key"]
        for s in d["software_installations"]:
            if s["assetId"] == a["id"] and (s["vendor"], s["product"], s["version"]) == old:
                s["vendor"], s["product"], s["version"] = a["vendor"], a["product"], a["version"]
        for rid in row_by_asset.get(a["id"], []):
            raw[rid]["payload"].update({"제조사": a["vendor"], "제품": a["product"], "버전": a["version"]})
    return [a["id"] for a in chosen]


# ---------- 조사값(공식 자료로 확인한 지원 종료일·패치 수준) ----------
def apply_research(assets, software, research, rng):
    if not research:
        return 0
    hits = 0
    index = {(e["match"]["vendor"], e["match"]["product"], e["match"].get("version")): e for e in research["entries"]}
    sw_by_asset = {}
    for s in software:
        sw_by_asset.setdefault(s["assetId"], []).append(s)
    for a in assets:
        e = index.get((a["vendor"], a["product"], a["version"])) or index.get((a["vendor"], a["product"], None))
        if not e:
            continue
        hits += 1
        if e.get("supportEndDate") or e.get("supportEndSource"):
            a["supportEnd"] = {k: e.get(k2) for k, k2 in (("date", "supportEndDate"), ("source", "supportEndSource"), ("confidence", "supportEndConfidence"), ("note", "supportEndNote"))}
        if e.get("noPublicVersion"):
            a["versionEvidence"] = "public_version_not_found"
        levels = e.get("patchLevels") or []
        if levels:
            lv = levels[min(len(levels) - 1, int(len(levels) * (rng.random() ** 1.6)))]    # 최신보다 뒤처진 쪽에 몰리게
            a["patchLevel"] = {k: lv.get(k) for k in ("label", "detail", "date", "source", "confidence")}
            a["patchLevelNote"] = "공개 자료의 실제 릴리스 번호를 가상 자산에 배분한 값이며 실제 장비의 값이 아니다"
            if re.match(r"\d{5}\.\d+$", str(lv.get("label"))):
                a["osBuild"] = lv["label"]
            if e.get("target") == "firmwareVersion":
                a["firmwareVersion"] = lv["label"]
                a["versionEvidence"] = "public_vendor_release_info_approximate"
                for s in sw_by_asset.get(a["id"], []):
                    if s.get("version") is None:
                        s["version"] = lv["label"]
    return hits


# ---------- 라인·MES ----------
def fix_lines(d):
    by_line = {}
    for e in d["equipment"]:
        by_line.setdefault(e["lineId"], []).append(e["id"])
    for l in d["lines"]:
        l["equipmentIds"] = by_line.get(l["id"], [])


def rebuild_mes(d, rng):
    code = d["code"]; base = dt.datetime.fromisoformat(R.OBS_START); as_of = base + dt.timedelta(hours=R.AS_OF_HOURS)
    parts = list(R.PARTS); wos, lots, per_line = [], [], {}
    idx = 0
    for li, line in enumerate(d["lines"]):
        offset = dt.timedelta(0)
        for k in range(R.WO_PER_LINE):
            idx += 1
            start = base + offset + dt.timedelta(hours=k * R.WO_HOURS); end = start + dt.timedelta(hours=R.WO_HOURS)
            part = parts[(idx + li) % len(parts)]
            planned = int(round(R.PARTS[part] * rng.uniform(0.8, 1.2) / 10) * 10)
            status = "completed" if end <= as_of else ("running" if start <= as_of else "released")
            actual = {"completed": int(planned * rng.uniform(0.92, 1.0)),
                      "running": int(planned * max(0.0, (as_of - start) / (end - start)) * 0.95), "released": None}[status]
            hour = start.hour
            wo = {"id": f"{code}-WO{idx:05d}", "lineId": line["id"], "partNumber": part, "plannedQuantity": planned, "status": status,
                  "plannedStart": start.isoformat(), "plannedEnd": end.isoformat(), "shiftAtStart": "A" if 6 <= hour < 14 else ("B" if 14 <= hour < 22 else "C"),
                  "actualQuantity": actual, "provenance": "synthetic_design_v2"}
            wos.append(wo); per_line.setdefault(line["id"], []).append(wo)
            lots.append({"id": f"{code}-LOT{idx:05d}", "workOrderId": wo["id"], "materialLot": f"SIM-MAT-{(idx - 1) // 3 + 1:04d}",
                         "provenance": "synthetic_design_v2"})
    d["mes_work_orders"], d["mes_lots"] = wos, lots
    lot_of = {l["workOrderId"]: l["id"] for l in lots}
    line_of = {e["id"]: e["lineId"] for e in d["equipment"]}
    groups = {}
    for o in d["machine_observations"]:
        groups.setdefault(o["equipmentId"], []).append(o)
    span = (as_of - base).total_seconds()
    for eq_id, items in groups.items():
        n = len(items)
        for i, o in enumerate(items):
            t = base + dt.timedelta(seconds=span * (i + 0.5 + rng.uniform(-0.3, 0.3)) / n)
            wo = next(w for w in per_line[line_of[eq_id]] if dt.datetime.fromisoformat(w["plannedStart"]) <= t < dt.datetime.fromisoformat(w["plannedEnd"]))
            o["simulatedTimestamp"] = t.replace(microsecond=0).isoformat()
            o["workOrderId"], o["lotId"] = wo["id"], lot_of[wo["id"]]
            o["assignmentProvenance"] = "synthetic_link_v2"
    return as_of.isoformat()


# ---------- 오염된 원본 대장 ----------
def excel_coerce(expected):
    if re.fullmatch(r"\d+\.\d+", expected):
        return f"{float(expected):.6f}"
    m = re.match(r"\d+(\.\d+)?", expected)
    if expected.isdigit():
        return expected + ".0"
    return f"{float(m.group(0)):.2f}" if m else expected


def vary_reported(d, rng):
    raw = {r["id"]: r for r in d["raw_asset_register"]}
    for i in d["quality_truth"]["issues"]:
        t = i["issueType"]
        if t in R.VARIANTS:
            new = rng.choice(R.VARIANTS[t])
        elif t == "departed_owner":
            new = rng.choice(R.DEPARTED_FORMATS).format(o=i["expected"])
        elif t == "excel_coercion":
            new = excel_coerce(str(i["expected"]))
        else:
            continue
        i["reported"] = new
        raw[i["rowId"]]["payload"][i["field"]] = new


def reassign_sources(d, rng):
    cat = {a["id"]: ("IT" if a["assetType"] in R.IT_TYPES else "OT") for a in d["canonical_assets"]}
    r2a = d["quality_truth"]["row_to_asset"]; files = list(R.FILE_FOR.values()) + ["협력사_인수인계.csv"]
    for r in d["raw_asset_register"]:
        if r["id"].endswith("-DUP"):
            continue
        c = cat[r2a[r["id"]]]
        want = R.FILE_FOR["IT"] if c == "IT" else rng.choice([R.FILE_FOR["OT"], "협력사_인수인계.csv"])
        r["source"] = rng.choice([f for f in files if f != want]) if rng.random() < R.CROSS_LEAK else want
    renumber(d)


def renumber(d):
    counters = {}
    for r in d["raw_asset_register"]:
        counters[r["source"]] = counters.get(r["source"], 0) + 1
        r["sourceRow"] = counters[r["source"]] + 1


def add_cross_file_conflicts(d, rng):
    by_id = {a["id"]: a for a in d["canonical_assets"]}
    base_rows = [r for r in d["raw_asset_register"] if not r["id"].endswith("-DUP")]
    for r in rng.sample(base_rows, round(len(by_id) * R.CROSS_FILE_RATE)):
        other = rng.choice([f for f in {x["source"] for x in base_rows} if f != r["source"]])
        p = dict(r["payload"])
        p["버전"] = rng.choice(["", "미상", "22H2", "2019", "3.0"]) if not p["버전"] or p["버전"] in ("", "-") else p["버전"] + ".1"
        p["담당"] = f"{d['code']}-IT" if str(p["담당"]).endswith("OT") else f"{d['code']}-OT"
        new = {"id": r["id"] + "-X", "source": other, "sourceRow": 9000 + len(d["raw_asset_register"]),
               "collectedAt": "2026-09-1%d" % rng.randint(0, 9) + "T09:00:00+09:00", "payload": p}
        d["raw_asset_register"].append(new)
        d["quality_truth"]["row_to_asset"][new["id"]] = d["quality_truth"]["row_to_asset"][r["id"]]
        d["quality_truth"]["issues"].append({"rowId": new["id"], "field": "record", "issueType": "cross_file_conflict",
                                              "expected": d["quality_truth"]["row_to_asset"][r["id"]], "reported": "다른 파일의 같은 자산과 버전·담당 값이 다름",
                                              "resolution": "human_review"})


# ---------- 요약과 검사 ----------
def diversify_flows(d, rng):
    """제조사 고유 통신 흐름을 섞는다. 포트는 흔히 쓰는 예시이며 실제 설정·지원 여부는 미검증이다."""
    assets = {a["id"]: a for a in d["canonical_assets"]}
    changed = 0
    for f in d["application_flows"]:
        src = assets.get(f["sourceAssetId"], {})
        rule = R.VENDOR_FLOWS.get(src.get("vendor"))
        if f["port"] == 4840 and rule and rng.random() < R.VENDOR_FLOW_SHARE:
            f["port"], f["purpose"] = rule["port"], rule["purpose"]
            f["provenance"] = "synthetic_variation_v2"
            f["note"] = rule["note"]
            changed += 1
    return changed


def update_summary(d, as_of, hetero_ids, research_hits):
    s = d["summary"]; q = d["quality_truth"]["issues"]
    s["rawRows"] = len(d["raw_asset_register"]); s["issues"] = len(q)
    s["issueTypes"] = dict(sorted(collections.Counter(i["issueType"] for i in q).items()))
    d["schemaVersion"] = "2.0-draft"
    d["v2"] = {"generator": "generate_v2.py", "seed": R.SEED, "asOfProgress": as_of, "heterogeneityAssets": hetero_ids,
               "researchedAssets": research_hits, "note": "원본 대비 파생 데이터. 변형 값은 시험용 가정이며 실제 회사 자료가 아니다."}


def validate(d):
    ids = {a["id"] for a in d["canonical_assets"]}; eq = {e["id"]: e for e in d["equipment"]}; lines = {l["id"] for l in d["lines"]}
    wos = {w["id"]: w for w in d["mes_work_orders"]}; lots = {l["id"]: l for l in d["mes_lots"]}
    base = dt.datetime.fromisoformat(R.OBS_START)
    checks = {
        "자산 ID 유일": len(ids) == len(d["canonical_assets"]),
        "lines가 모든 설비 연결": sorted(x for l in d["lines"] for x in l["equipmentIds"]) == sorted(eq),
        "WO→라인": all(w["lineId"] in lines for w in wos.values()),
        "LOT→WO 1:1": all(l["workOrderId"] in wos for l in lots.values()) and len(lots) == len(wos),
        "관측 참조": all(o["equipmentId"] in eq and o["workOrderId"] in wos and o["lotId"] in lots for o in d["machine_observations"]),
        "미시작 WO 관측 0": not any(wos[o["workOrderId"]]["status"] == "released" for o in d["machine_observations"]),
        "관측이 WO 시간 안": all(dt.datetime.fromisoformat(wos[o["workOrderId"]]["plannedStart"]) <= dt.datetime.fromisoformat(o["simulatedTimestamp"]) < dt.datetime.fromisoformat(wos[o["workOrderId"]]["plannedEnd"]) for o in d["machine_observations"]),
        "소프트웨어→자산": all(s["assetId"] in ids for s in d["software_installations"]),
        "흐름→자산": all(f["sourceAssetId"] in ids and f["targetAssetId"] in ids for f in d["application_flows"]),
        "raw→정답 연결": all(r["id"] in d["quality_truth"]["row_to_asset"] for r in d["raw_asset_register"]),
        "issue→raw 행": all(i["rowId"] in {r["id"] for r in d["raw_asset_register"]} for i in d["quality_truth"]["issues"]),
        "MES 예외→LOT/WO": all(e["lotId"] in lots and e["expectedWorkOrderId"] in wos for e in d["raw_mes_exceptions"]),
        "기간 하루 이상": max(dt.datetime.fromisoformat(o["simulatedTimestamp"]) for o in d["machine_observations"]) - base > dt.timedelta(hours=24),
    }
    return checks


def build(code, src, out, research):
    d = json.loads((src / f"{code.lower()}_factory.json").read_text(encoding="utf-8"))
    original_obs = copy.deepcopy([o["original"] for o in d["machine_observations"]])
    rng = random.Random(f"{R.SEED}-{code}")
    vary_attributes(d["canonical_assets"], rng)
    add_exposure_edr_reboot(d["canonical_assets"], d["lines"], rng)
    hetero_ids = apply_heterogeneity(d, rng)
    hits = apply_research(d["canonical_assets"], d["software_installations"], research, rng)
    diversify_flows(d, rng)
    fix_lines(d)
    as_of = rebuild_mes(d, rng)
    vary_reported(d, rng); reassign_sources(d, rng); add_cross_file_conflicts(d, rng); renumber(d)
    update_summary(d, as_of, hetero_ids, hits)
    checks = validate(d); checks["AI4I 원본값 보존"] = original_obs == [o["original"] for o in d["machine_observations"]]
    (out / f"{code.lower()}_factory_v2.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return checks, hits


def main(src, out, research_path=None):
    src, out = pathlib.Path(src), pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    research = json.loads(pathlib.Path(research_path).read_text(encoding="utf-8")) if research_path and pathlib.Path(research_path).exists() else None
    for code in ("VMA", "VMB", "VMC"):
        checks, hits = build(code, src, out, research)
        print(code, "조사값 적용 자산", hits, "|", "통과" if all(checks.values()) else "실패", {k: v for k, v in checks.items() if not v} or "")


if __name__ == "__main__":
    main(*sys.argv[1:4])
