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
            if key == "criticality" and a.get("process"):
                continue
            if t in table:
                new = weighted(rng, table[t])
                if new != a[key]:
                    a[key] = new; changed.append(key)
        if rng.random() < R.ROLLBACK_TRUE_CHANCE.get(t, 0):
            a["rollbackPossible"] = True; changed.append("rollbackPossible")
        if rng.random() < R.ROLLBACK_FALSE_CHANCE.get(t, 0):
            a["rollbackPossible"] = False; changed.append("rollbackPossible")
        cons = list(a["patchConstraints"])
        if not a.get("process"):
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
        if e.get("discontinuedOn"):
            a["discontinuedOn"] = {"date": e["discontinuedOn"], "source": e.get("discontinuedSource"), "confidence": e.get("discontinuedConfidence"), "note": e.get("discontinuedNote")}
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


# ---------- 제품 카탈로그(실제 제품·버전·공지)를 가상 자산에 연결 ----------
CATALOG_KEYS = {
    ("Microsoft", "Windows 10 Enterprise", "22H2"): "win10_22h2", ("Microsoft", "Windows 10 IoT Enterprise LTSC", "2021"): "win10_ltsc2021",
    ("Microsoft", "Windows 11", "23H2"): "win11_23h2", ("Microsoft", "Windows Server", "2019"): "winsrv2019",
    ("Microsoft", "Windows Server", "2022"): "winsrv2022", ("VMware", "ESXi", "7.0"): "esxi", ("VMware", "ESXi", "6.7"): "esxi",
    ("Veeam", "Backup & Replication", "12"): "veeam12", ("Fortinet", "FortiOS", "7.2"): "fortios",
    ("Palo Alto Networks", "PAN-OS", "10.2"): "panos", ("Cisco", "Catalyst 9300", None): "iosxe",
    ("Siemens", "SIMATIC S7-1500", None): "s7_1500", ("Siemens", "SINUMERIK 840D sl", None): "sinumerik",
    ("Mitsubishi Electric", "MELSEC iQ-R R04CPU", None): "iqr", ("FANUC", "R-30iB Plus", None): "fanuc", ("Moxa", "EDS-516A", None): "eds516a",
    ("LS ELECTRIC", "XGK-CPUU", None): "ls_xgk", ("LS ELECTRIC", "XGI-CPUU", None): "ls_xgi", ("LS ELECTRIC", "XBC-DN32U", None): "ls_xbc",
    ("PTC Kepware", "KEPServerEX", None): "kepserverex", ("Inductive Automation", "Ignition", "8.0"): "ignition",
    ("Inductive Automation", "Ignition", "8.1"): "ignition", ("Siemens", "SIMATIC WinCC", None): "wincc",
}


def version_key(text):
    """버전 문자열을 비교 가능한 숫자 튜플로 바꾼다. 17.9.4a, 10.2.9-h1, 19045.4780, '빌드 N'을 다룬다."""
    m = re.search(r"빌드 (\d+)", text)
    if m:
        return (int(m.group(1)),)
    nums = [int(x) for x in re.findall(r"\d+", text.split("-h")[0])]
    letter = re.search(r"\d([a-z])$", text)
    hotfix = re.search(r"-h(\d+)$", text)
    return tuple(nums) + ((ord(letter.group(1)) - 96,) if letter else (0,) if "." in text and nums else ()) + ((int(hotfix.group(1)),) if hotfix else ())


def judge(advisory, line, version):
    """영향 여부를 판정한다: affected_scenario / affected_no_fix / fixed / not_listed / unknown."""
    if line not in advisory["affected"]:
        return "not_listed"
    v = version_key(version)
    if advisory.get("affectedFrom") and v < version_key(advisory["affectedFrom"]):
        return "not_listed"
    if advisory.get("noFix"):
        return "affected_no_fix"
    fixes = advisory["fixed"].get(line)
    if not fixes:
        return "unknown"
    return "fixed" if v >= min(version_key(f) for f in fixes) else "affected_scenario"


def synthetic_epss(cve, kev):
    """EPSS 값은 실제 값을 가져올 수 없어 시험용 값으로 만든다(synthetic 표시). KEV 등재 건은 높게 둔다."""
    r = random.Random(f"{R.SEED}-epss-{cve}")
    score = r.uniform(0.30, 0.95) if kev else r.uniform(0.001, 0.20)
    return {"score": round(score, 4), "date": R.EPSS_DATE, "synthetic": True}


def source_confidence(source):
    if "VENDOR" in source or "MSRC" in source:
        return "high"
    return "low" if source.strip() == "SUMMARY" else "medium"


def match_advisory(adv, line, version):
    status = judge(adv, line, version)
    if status == "affected_scenario" and adv.get("precondition"):
        status = "affected_conditional"
    m = {"cve": adv["cve"], "status": status, "kev": adv["kev"], "kevAdded": adv["kevAdded"], "url": adv["url"],
         "cvss": adv["cvss"], "epss": synthetic_epss(adv["cve"], adv["kev"]), "confidence": source_confidence(adv["source"]),
         "scenario": True}
    if adv.get("precondition"):
        m["precondition"] = adv["precondition"]
    if adv.get("note"):
        m["note"] = adv["note"]
    return m


def support_end_year(asset):
    date = (asset.get("supportEnd") or {}).get("date")
    return int(date[:4]) if date else None


def apply_catalog(assets, catalog, research, rng, expected):
    if not catalog:
        return 0
    products = {p["key"]: p for p in catalog["products"]}
    research_levels = {lv["label"]: lv for e in (research or {}).get("entries", []) for lv in e.get("patchLevels", [])}
    done = 0
    for a in assets:
        key = CATALOG_KEYS.get((a["vendor"], a["product"], a["version"]))
        if not key:
            continue
        pr = products[key]
        if pr.get("firmware") and rng.random() < R.UNKNOWN_FIRMWARE_CHANCE:
            a["versionEvidence"] = "unknown_firmware_or_version"
            a["fleetMixV2"] = "synthetic_assumption(firmware_unknown)"
            continue
        year = a.get("installedYear") or rng.choice([2018, 2019, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2024, 2025])
        end_year = support_end_year(a)
        if end_year:
            year = min(year, end_year)
        if a.get("version") is None:
            options = [l for l in pr["lines"] if (l["ga"] or 0) <= year] or pr["lines"][:1]
            line = options[int(len(options) * (rng.random() ** 0.8))]
        else:
            line = next((l for l in pr["lines"] if l["line"] == a["version"]), None)
        if not line:
            continue
        base_year = year
        year = max(year, line["ga"] or 0)
        if year > base_year and a.get("installedYear"):
            a["osReinstalledYear"] = year
        version = pick_by_date(line, year, rng, a.get("category", "IT"), R.OT_UPDATED_BY_WAVE.get(a.get("lineWave")))
        if version is None:
            cands = line["candidates"]
            idx = len(cands) - 1 if rng.random() < 0.2 else int(len(cands) * (rng.random() ** (1.4 if year >= 2023 else 0.8)))
            version = cands[min(idx, len(cands) - 1)]
        a["installedYear"] = year
        matches = [] if a.get("lifecycle") == "retired" else [match_advisory(adv, line["line"], version) for adv in pr["advisories"]]
        expected.append({"assetId": a["id"], "product": key, "line": line["line"], "version": version,
                         "lifecycle": a.get("lifecycle"), "matches": matches})
        if key.startswith("win"):
            a["osBuild"] = version
        if pr.get("firmware"):
            a["firmwareVersion"] = version
        a["versionEvidence"] = "catalog_public_version_assigned"
        prev = research_levels.get(version, {})
        a["patchLevel"] = {"label": version, "detail": prev.get("detail") or "카탈로그 후보 중 배정", "date": prev.get("date"),
                           "source": prev.get("source") or "product_catalog.json", "confidence": prev.get("confidence") or "카탈로그 후보(번호만)"}
        a["patchLevelNote"] = "공개된 실제 버전 번호를 도입 연도와 갱신 상황을 가정해 가상 자산에 배정한 값이며 실제 장비의 값이 아니다"
        if end_year and (a["supportEnd"].get("date") or "")[:7] < R.AS_OF_MONTH:
            a["supportStatus"] = "ended"
            a["supportStatusNote"] = "지원 종료 뒤 빌드는 ESU 등 별도 계약이 있는지 확인 필요(모델링하지 않음)"
        a["scenario"] = True
        a["scenarioNotice"] = "가상 회사 자산. 제품·버전은 실제 공개 버전 번호를 가정해 배정한 값이며 실제 회사·장비의 값이 아니다"
        a["fieldProvenance"] = {"installedYear": "synthetic_assumption", "patchLevel": "public_version_assigned_by_assumption",
                                "supportEnd": "public_source_see_supportEnd.confidence"}
        done += 1
    return done


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
        p["담당"] = f"{d['code']}-OT" if str(p["담당"]).startswith(f"{d['code']}-IT") else f"{d['code']}-IT"
        new = {"id": r["id"] + "-X", "source": other, "sourceRow": 9000 + len(d["raw_asset_register"]),
               "collectedAt": "2026-09-1%d" % rng.randint(0, 9) + "T09:00:00+09:00", "payload": p}
        d["raw_asset_register"].append(new)
        d["quality_truth"]["row_to_asset"][new["id"]] = d["quality_truth"]["row_to_asset"][r["id"]]
        d["quality_truth"]["issues"].append({"rowId": new["id"], "field": "record", "issueType": "cross_file_conflict",
                                              "expected": d["quality_truth"]["row_to_asset"][r["id"]], "reported": "다른 파일의 같은 자산과 버전·담당 값이 다름",
                                              "resolution": "human_review"})


# ---------- 요약과 검사 ----------
def add_extra_assets(d, rng):
    """빠진 설비 자산을 사이트마다 추가한다. 수기 대장에는 없는 자산으로 두어 대장 누락 사례가 된다."""
    assets = d["canonical_assets"]
    next_id = max(int(a["id"].rsplit("A", 1)[1]) for a in assets) + 1
    used = {a["ip"] for a in assets if a.get("ip")}
    seg_by_id = {s["id"]: s for s in d["network_segments"]}
    added = []
    for site in sorted({a["siteId"] for a in assets}):
        code = d["owners"][0]["id"].split("-")[0]
        for kind, count, cat, seg, owner, product, crit, cons, exposure, rb in R.EXTRA_ASSETS:
            segment = seg_by_id[f"{site}-{seg}"]
            prefix = segment["cidr"].rsplit(".", 1)[0]
            for n in range(1, count + 1):
                host = 100
                while f"{prefix}.{host}" in used:
                    host += 1
                ip = f"{prefix}.{host}"; used.add(ip)
                aid = f"{code}-A{next_id:05d}"; next_id += 1
                assets.append({
                    "id": aid, "companyId": code, "siteId": site, "name": f"{site} {kind} {n}", "assetType": kind,
                    "vendor": R.EXTRA_VENDOR, "product": product, "version": None, "category": cat,
                    "criticality": crit, "zone": segment["name"], "line": "공용", "affectedEquipment": f"{site} {kind} {n}",
                    "networkSegmentId": segment["id"], "ip": ip, "ownerId": f"{code}-{owner}", "lifecycle": "active",
                    "lastVerifiedAt": None, "patchConstraints": list(cons), "rollbackPossible": rb,
                    "versionEvidence": "not_modeled", "exactBuildKnown": False, "serial": f"SIM-{aid}",
                    "provenance": "synthetic_design_v2", "exposure": exposure, "edr": None,
                    "rebootWindow": rng.choice(R.REBOOT_OT if cat == "OT" else R.REBOOT_IT),
                    "registerStatus": "not_in_register",
                    "fieldsV2Provenance": "synthetic_assumption(new asset type added from critique; not in manual register)",
                })
                added.append(aid)
    return added


def _clean_rows(d):
    """자산별 대장 행과 '오류가 표시된 필드'(→ 오류 객체)를 모은다. 없애기로 표시한 오류는 제외한다."""
    rows, flagged = {}, {}
    for rid, aid in d["quality_truth"]["row_to_asset"].items():
        rows.setdefault(aid, []).append(rid)
    for i in d["quality_truth"]["issues"]:
        if not i.get("_drop"):
            flagged[(i["rowId"], i["field"])] = i
    return rows, flagged


def _blocked(rows, flagged, aid, fields):
    return any((rid, f) in flagged for rid in rows.get(aid, []) for f in fields)


def _set_payload(raw, rows, aid, field, old, new):
    for rid in rows.get(aid, []):
        p = raw[rid]["payload"]
        if str(p.get(field, "")).strip().lower() == str(old).strip().lower():     # 공백·대소문자 변형 행도 같이 바꾼다
            p[field] = new


def _abbreviate(product):
    return "WIN " + product.split(" ", 1)[1] if product.startswith("Windows ") else product.replace(" ", "").replace("-", "")


def _remap_issues(a, new, rows, flagged, raw):
    """제조사·제품·버전에 표시된 오류를 새 값에 맞게 바꾼다(별칭·약어는 다시 만들고 나머지는 없앤다)."""
    for rid in rows.get(a["id"], []):
        for field, value in (("제조사", new[0]), ("제품", new[1]), ("버전", new[2] or "")):
            issue = flagged.get((rid, field))
            if not issue:
                continue
            if issue["issueType"] == "vendor_alias":
                issue["expected"] = value
                issue["reported"] = f"  {value.upper()} "
            elif issue["issueType"] == "product_abbreviation":
                issue["expected"] = value
                issue["reported"] = _abbreviate(value)
            else:
                issue["_drop"] = True
                raw[rid]["payload"][field] = value
                continue
            raw[rid]["payload"][field] = issue["reported"]


def _num(pattern, items, key):
    """식별자에서 번호를 뽑아 최댓값을 구한다."""
    nums = [int(m.group(1)) for x in items if (m := re.search(pattern, x[key]))]
    return max(nums) if nums else 0


def plan_growth(lines, founding_year, last_year, rng, shares, ops_by_type):
    if not lines:
        return

    n = len(lines)
    f = min(rng.choice([2, 3]), n)

    init_types = ["가공", "가공"] if f == 2 else ["가공", "가공", "세척·검사"]
    init_types = init_types[:f]

    m = n - f
    rem_years = []
    if m > 0:
        for k in range(m):
            y = founding_year + 1 + int(k * (last_year - founding_year) / m + rng.uniform(-0.3, 0.3))
            y = max(founding_year + 1, min(last_year, y))
            rem_years.append(y)
        rem_years.sort()

    all_years = [founding_year] * f + rem_years

    target_counts = {}
    allocated = 0
    for i, (t, r) in enumerate(shares):
        if i == len(shares) - 1:
            cnt = n - allocated
        else:
            cnt = round(n * r)
            allocated += cnt
        target_counts[t] = cnt

    rem_counts = {}
    for t, _ in shares:
        rem_counts[t] = target_counts.get(t, 0)
    for t in init_types:
        rem_counts[t] = max(0, rem_counts.get(t, 0) - 1)

    pattern = ["가공", "세척·검사", "가공", "조립·포장"]
    rem_types = []
    for idx in range(m):
        pref = pattern[idx % 4]
        if rem_counts.get(pref, 0) > 0:
            chosen = pref
        else:
            candidates = [(t, rem_counts.get(t, 0)) for t, _ in shares if rem_counts.get(t, 0) > 0]
            if candidates:
                chosen = max(candidates, key=lambda x: x[1])[0]
            else:
                chosen = "가공"
        rem_types.append(chosen)
        if rem_counts.get(chosen, 0) > 0:
            rem_counts[chosen] -= 1

    all_types = init_types + rem_types

    generations = []
    curr_gen = 0
    for i in range(n):
        if i < f:
            generations.append(0)
        else:
            if all_years[i] != all_years[i - 1]:
                curr_gen += 1
            generations.append(curr_gen)

    for i in range(n):
        lines[i]["lineType"] = all_types[i]
        lines[i]["operations"] = list(ops_by_type[all_types[i]])
        lines[i]["commissionYear"] = all_years[i]
        lines[i]["generation"] = generations[i]


def restructure_lines(d):
    """라인을 가공 / 세척·검사 / 조립·포장 유형으로 나누고 유형마다 설비 종류와 수를 다르게 한다.

    남는 자산(와 딸린 대장 행·설치 목록·통신·스위치 포트·설비)은 지우고 모자라는 자산은 같은 라인의 같은 종류를 본떠 만든다.
    CNC는 내장 패널을 쓰므로 조작 PC(HMI)는 라인당 1~2대 공용으로 줄인다. 공정(`process`)과 이중화(`redundancy`)를 자산에 붙인다.
    """
    rng = random.Random(f"{R.SEED}-{d['code']}-restructure")
    code = d["code"]
    assets = d["canonical_assets"]
    raw = {r["id"]: r for r in d["raw_asset_register"]}
    r2a = d["quality_truth"]["row_to_asset"]
    next_a = _num(r"A(\d+)$", assets, "id") + 1
    next_raw = _num(r"RAW(\d+)", d["raw_asset_register"], "id") + 1
    next_flow = _num(r"F(\d+)$", d["application_flows"], "id") + 1
    next_eq = _num(r"E(\d+)$", d["equipment"], "id") + 1
    used_ips = collections.defaultdict(set)
    for a in assets:
        if a.get("ip"):
            used_ips[a["networkSegmentId"]].add(a["ip"])
    seg = {s["id"]: s for s in d["network_segments"]}
    stat = collections.Counter()

    # 라인 성장 계획(개설 연도·세대·유형)
    by_site = {}
    for l in d["lines"]:
        by_site.setdefault(l["siteId"], []).append(l)
    ops = {k: v["ops"] for k, v in R.LINE_TYPES.items()}
    for site, lines in by_site.items():
        plan_growth(lines, R.FOUNDING_YEAR.get(site, R.FOUNDING_DEFAULT), R.LAST_LINE_YEAR, rng, R.LINE_TYPE_SHARE, ops)

    removed = set()
    created = []
    for line in d["lines"]:
        spec = R.LINE_TYPES[line["lineType"]]
        in_line = {}
        for a in sorted((x for x in assets if x["line"] == line["id"]), key=lambda x: x["id"]):
            in_line.setdefault(a["assetType"], []).append(a)
        for kind, (lo, hi) in spec["counts"].items():
            target = rng.randint(lo, hi)
            have = in_line.get(kind, [])
            for extra in have[target:]:
                removed.add(extra["id"])
            if len(have) < target and have:
                for _ in range(target - len(have)):
                    new = copy.deepcopy(have[0])
                    new["id"] = f"{code}-A{next_a:05d}"
                    new["serial"] = f"SIM-{code}-{next_a:06d}"
                    next_a += 1
                    free = [h for h in range(11, 250) if f"{seg[new['networkSegmentId']]['cidr'].rsplit('.', 1)[0]}.{h}" not in used_ips[new["networkSegmentId"]]]
                    new["ip"] = f"{seg[new['networkSegmentId']]['cidr'].rsplit('.', 1)[0]}.{rng.choice(free)}"
                    used_ips[new["networkSegmentId"]].add(new["ip"])
                    new["provenance"] = "synthetic_design_v2"
                    new["_template"] = have[0]["id"]
                    created.append(new)
                    in_line[kind] = in_line.get(kind, []) + [new]
        line["_kept"] = {k: [a for a in v if a["id"] not in removed] for k, v in in_line.items()}
    stat["삭제한 자산"] = len(removed)
    stat["새로 만든 자산"] = len(created)

    # 삭제: 자산, 대장 행·오류, 설치 목록, 통신, 스위치 포트, 설비
    drop_rows = {rid for rid, aid in r2a.items() if aid in removed}
    d["canonical_assets"] = [a for a in assets if a["id"] not in removed] + created
    assets = d["canonical_assets"]
    d["raw_asset_register"] = [r for r in d["raw_asset_register"] if r["id"] not in drop_rows]
    for rid in drop_rows:
        r2a.pop(rid, None)
    d["quality_truth"]["issues"] = [i for i in d["quality_truth"]["issues"] if i["rowId"] not in drop_rows]
    d["software_installations"] = [s for s in d["software_installations"] if s["assetId"] not in removed]
    d["application_flows"] = [f for f in d["application_flows"] if f["sourceAssetId"] not in removed and f["targetAssetId"] not in removed]
    d["line_port_bindings"] = [b for b in d["line_port_bindings"] if b["assetId"] not in removed and b["switchAssetId"] not in removed]
    kept_eq = [e for e in d["equipment"] if e["controlAssetId"] not in removed]

    # 새 자산의 설치 목록·통신·스위치 포트
    sw_by = collections.defaultdict(list)
    for s in d["software_installations"]:
        sw_by[s["assetId"]].append(s)
    flows_by = collections.defaultdict(list)
    for f in d["application_flows"]:
        flows_by[f["sourceAssetId"]].append(f)
    bind_count = collections.Counter(b["switchAssetId"] for b in d["line_port_bindings"])
    used_ports = collections.defaultdict(set)
    for b in d["line_port_bindings"]:
        used_ports[b["switchAssetId"]].add(b["port"])
    sw_counter = collections.Counter({k: len(v) for k, v in sw_by.items()})
    for a in created:
        tmpl = a.pop("_template")
        for s in list(sw_by.get(tmpl, [])):
            sw_counter[a["id"]] += 1
            d["software_installations"].append({**s, "id": f"{a['id']}-SW{sw_counter[a['id']]:02d}", "assetId": a["id"]})
        for f in list(flows_by.get(tmpl, [])):
            d["application_flows"].append({**f, "id": f"{code}-F{next_flow:05d}", "sourceAssetId": a["id"]})
            next_flow += 1
        switches = [x for x in assets if x["line"] == a["line"] and x["assetType"] == "산업용 스위치"]
        if switches:
            sw_asset = min(switches, key=lambda x: bind_count[x["id"]])
            port = min(p for p in range(1, 15) if p not in used_ports[sw_asset["id"]])
            used_ports[sw_asset["id"]].add(port)
            bind_count[sw_asset["id"]] += 1
            d["line_port_bindings"].append({"assetId": a["id"], "switchAssetId": sw_asset["id"], "port": port, "reservedUplinkPorts": [15, 16], "provenance": "synthetic_design_v2"})

    # 공정·이중화 표시와 이름
    def rename(a, new):
        old = a["name"]
        if old == new:
            return
        a["name"] = a["affectedEquipment"] = new
        for rid, aid in r2a.items():
            if aid != a["id"] or rid not in raw:
                continue
            p = raw[rid]["payload"]
            for i in d["quality_truth"]["issues"]:
                if i["rowId"] == rid and i["field"] == "설비명":
                    suffix = i["reported"][len(i["expected"]):] if i["reported"].startswith(i["expected"]) else " / 확인필요"
                    i["expected"], i["reported"] = new, new + suffix
                    p["설비명"] = i["reported"]
                    break
            else:
                if str(p.get("설비명", "")).strip() == old:
                    p["설비명"] = new

    for line in d["lines"]:
        tp = line["lineType"]
        kept = {k: sorted(v, key=lambda x: x["id"]) for k, v in line.pop("_kept").items()}
        lid = line["id"]
        plcs = kept.get("PLC", [])
        n = len(plcs)
        roles = {"가공": list(R.LINE_TYPES["가공"]["ops"]), "세척·검사": ["세척"] * (n - 1) + ["컨베이어"],
                 "조립·포장": ["조립"] * max(n - 2, 0) + ["포장"] * min(n, 2)}[tp]
        proc = {}
        for k, a in enumerate(plcs):
            proc[a["id"]] = roles[k]
        inv_roles = {"가공": ["소재 투입", "디버링"], "세척·검사": ["세척"] * 99, "조립·포장": ["포장"] * 99}[tp]
        for k, a in enumerate(kept.get("인버터", [])):
            proc[a["id"]] = inv_roles[k] if k < len(inv_roles) else inv_roles[-1]
        for a in kept.get("CNC 컨트롤러", []):
            proc[a["id"]] = "절삭·밀링"
        for a in kept.get("로봇 컨트롤러", []):
            proc[a["id"]] = "절삭·밀링" if tp == "가공" else "조립"
        for a in kept.get("비전 검사 PC", []):
            proc[a["id"]] = "조립" if tp == "조립·포장" else "치수·비전 검사"
        for a in kept.get("바코드 리더", []):
            proc[a["id"]] = {"가공": "소재 투입", "세척·검사": "치수·비전 검사", "조립·포장": "포장"}[tp]
        for kind in ("산업용 스위치", "HMI PC", "엣지 수집 PC", "안돈 단말"):
            for a in kept.get(kind, []):
                proc[a["id"]] = "라인 공용"
        counters = collections.Counter()
        kind_count = collections.Counter()
        for kind, items in kept.items():
            for a in items:
                a["process"] = proc[a["id"]]
                a["bottleneck"] = a["process"] == R.LINE_TYPES[tp]["bottleneck"]
                group = [x for x in items if proc[x["id"]] == a["process"]]
                a["redundancy"] = "parallel" if len(group) >= 2 else "none"
                counters[(kind, a["process"])] += 1
                k = counters[(kind, a["process"])]
                if kind == "PLC":
                    rename(a, f"{lid} {a['process']} PLC {k:02d}")
                elif kind == "HMI PC":
                    rename(a, f"{lid} 공용 HMI {k:02d}")
                elif kind == "CNC 컨트롤러":
                    rename(a, f"{lid} CNC {k:02d} 제어기")
                elif kind in ("로봇 컨트롤러", "인버터", "비전 검사 PC", "산업용 스위치", "바코드 리더", "엣지 수집 PC", "안돈 단말"):
                    kind_count[kind] += 1
                    rename(a, f"{lid} {kind} {kind_count[kind]:02d}")
                a["osManagement"] = "vendor_bundled" if kind in ("CNC 컨트롤러", "PLC", "로봇 컨트롤러", "인버터", "산업용 스위치", "바코드 리더") else "customer_managed"

    # 새 자산의 대장 행(깨끗한 행으로 시작; 오류는 뒤 단계에서 일부만 생김)
    template_collected = d["raw_asset_register"][0]["collectedAt"]
    for a in created:
        rid = f"{code}-RAW{next_raw:05d}"
        next_raw += 1
        d["raw_asset_register"].append({"id": rid, "source": "설비대장_최종.xlsx", "sourceRow": 0, "collectedAt": template_collected,
                                        "payload": {"설비명": a["name"], "제조사": a["vendor"], "제품": a["product"], "버전": a["version"] or "", "IP": a["ip"] or "",
                                                    "담당": a["ownerId"] or "", "라인": a["line"], "시리얼": a["serial"], "상태": a["lifecycle"], "확인일": a["lastVerifiedAt"] or ""}})
        r2a[rid] = a["id"]

    # 설비(물리 설비) 다시 만들기
    by_ctrl = {e["controlAssetId"]: e for e in kept_eq}
    equipment = []
    for line in d["lines"]:
        lid = line["id"]
        cnt = collections.Counter()
        for a in sorted((x for x in d["canonical_assets"] if x["line"] == lid and x["assetType"] in R.EQUIPMENT_TYPES), key=lambda x: x["id"]):
            cnt[a["assetType"]] += 1
            kind = a["assetType"]
            label = {"CNC 컨트롤러": f"CNC 가공기 {cnt[kind]:02d}", "PLC": f"{a['process']} 셀 {cnt[kind]:02d}",
                     "로봇 컨트롤러": f"로봇 {cnt[kind]:02d}", "비전 검사 PC": f"비전 검사 {cnt[kind]:02d}"}[kind]
            e = by_ctrl.get(a["id"])
            if e is None:
                e = {"id": f"{code}-E{next_eq:05d}", "name": "", "siteId": a["siteId"], "lineId": lid, "controlAssetId": a["id"], "provenance": "synthetic_design_v2"}
                next_eq += 1
            e["name"] = f"{lid} {label}"
            equipment.append(e)
    d["equipment"] = equipment
    # 가공 관측은 CNC 설비에만 붙인다(AI4I 값은 그대로, 연결만 다시 한다)
    cnc_eq = [e["id"] for e in equipment if next(x for x in d["canonical_assets"] if x["id"] == e["controlAssetId"])["assetType"] == "CNC 컨트롤러"]
    for i, o in enumerate(d["machine_observations"]):
        o["equipmentId"] = cnc_eq[i % len(cnc_eq)]
    stat["CNC 설비"] = len(cnc_eq)
    return dict(stat)


def assign_process_attributes(d, rng):
    """공정(병목)·이중화·제조사로 중요도와 작업 제약을 정한다. 모든 설비가 같은 값이 되지 않게 한다."""
    for a in d["canonical_assets"]:
        if not a.get("process") or a["line"] == "공용":
            continue
        kind = a["assetType"]
        table = R.CRIT_BY_TYPE.get(kind) or R.CRIT_BY_PROCESS[(a["bottleneck"], a["redundancy"] == "parallel")]
        a["criticality"] = pick(rng, table)
        a["criticalityBasis"] = "synthetic_assumption(bottleneck_redundancy)"
        cons = []
        if rng.random() < R.MAINT_WINDOW_CHANCE:
            cons.append("maintenance_window")
        chance = R.VENDOR_APPROVAL_CHANCE.get(kind, 0.0)
        if kind == "PLC":
            chance = R.PLC_VENDOR_APPROVAL.get(a["vendor"], 0.40)
        if rng.random() < chance:
            cons.append("vendor_approval")
        if a["redundancy"] == "none" and rng.random() < (R.NO_DOWNTIME_SINGLE_BOTTLENECK if a["bottleneck"] else R.NO_DOWNTIME_SINGLE_OTHER):
            cons.append("no_downtime")
        a["patchConstraints"] = cons


def add_line_flows(d, rng):
    """라인 안의 통신(HMI·로봇·인버터·비전 → PLC, 엔지니어링 PC → PLC)을 추가한다. 포트는 제조사별 예시이며 실제 설정은 미검증."""
    code = d["code"]
    next_flow = _num(r"F(\d+)$", d["application_flows"], "id") + 1
    assets = d["canonical_assets"]
    by_line = {}
    for a in assets:
        by_line.setdefault(a["line"], []).append(a)
    added = 0

    def add(src, dst, port, purpose):
        nonlocal next_flow, added
        d["application_flows"].append({"id": f"{code}-F{next_flow:05d}", "sourceAssetId": src["id"], "targetAssetId": dst["id"], "protocol": "TCP",
                                       "port": port, "purpose": purpose, "approval": "synthetic_baseline", "provenance": "synthetic_variation_v2",
                                       "note": "포트는 제조사별로 널리 쓰는 예시이며 실제 설정·지원은 검증하지 않음"})
        next_flow += 1
        added += 1

    first_plc = {}
    for lid, items in by_line.items():
        plcs = sorted((a for a in items if a["assetType"] == "PLC"), key=lambda x: x["id"])
        if not plcs:
            continue
        first_plc[lid] = plcs[0]
        for k, hmi in enumerate(sorted((a for a in items if a["assetType"] == "HMI PC"), key=lambda x: x["id"])):
            for plc in plcs[:3]:
                add(hmi, plc, R.PLC_PORT.get(plc["vendor"], 502), "공용 HMI의 PLC 상태 조회·조작")
        for k, robot in enumerate(sorted((a for a in items if a["assetType"] == "로봇 컨트롤러"), key=lambda x: x["id"])):
            plc = plcs[k % len(plcs)]
            add(robot, plc, R.PLC_PORT.get(plc["vendor"], 502), "로봇과 PLC의 신호 교환")
        for inv in (a for a in items if a["assetType"] == "인버터"):
            same = [p for p in plcs if p["process"] == inv["process"]] or plcs
            add(inv, rng.choice(same), 502, "인버터 운전 지령(Modbus TCP 예시)")
        for vis in (a for a in items if a["assetType"] == "비전 검사 PC"):
            plc = rng.choice([p for p in plcs if p["process"] == vis["process"]] or plcs)
            add(vis, plc, R.PLC_PORT.get(plc["vendor"], 502), "비전 검사 결과 전달")
    lines = list(first_plc)
    for eng in (a for a in assets if a["assetType"] == "엔지니어링 PC"):
        for lid in rng.sample(lines, min(3, len(lines))):
            plc = first_plc[lid]
            add(eng, plc, R.PLC_PORT.get(plc["vendor"], 502), "엔지니어링 PC의 PLC 프로그램 접속")
    return added


def assign_owners(d, rng):
    """OT 라인 자산의 담당을 가공설비 보전조·후공정 보전조·협력사 상주로 나눈다(공용 OT는 기존 OT팀 그대로)."""
    code = d["code"]
    groups = {f"{code}-OT-MCH": "가상 가공설비 보전조", f"{code}-OT-FIN": "가상 후공정 보전조", f"{code}-VND": "가상 협력사 설비관리(현장 상주)"}
    d["owners"] += [{"id": k, "name": v, "role": "member"} for k, v in groups.items() if k not in {o["id"] for o in d["owners"]}]
    rows, flagged = _clean_rows(d)
    raw = {r["id"]: r for r in d["raw_asset_register"]}
    line_type = {l["id"]: l["lineType"] for l in d["lines"]}
    changed = 0
    for a in d["canonical_assets"]:
        if a["line"] == "공용" or a["category"] != "OT" or not a.get("ownerId"):
            continue
        if "vendor_approval" in a["patchConstraints"] and rng.random() < 0.6:
            new = f"{code}-VND"
        else:
            new = f"{code}-OT-MCH" if line_type[a["line"]] == "가공" else f"{code}-OT-FIN"
        old = a["ownerId"]
        if new == old:
            continue
        a["ownerId"] = new
        _set_payload(raw, rows, a["id"], "담당", old, new)
        for rid in rows.get(a["id"], []):
            issue = flagged.get((rid, "담당"))
            if issue:
                issue["expected"] = new
        changed += 1
    return changed


def randomize_identifiers(d, rng):
    """시리얼은 순번이 아닌 불규칙한 값으로, 라인 자산의 IP는 짝수 순번이 아닌 무작위 호스트 번호로 바꾼다."""
    code = d["code"]
    rows, flagged = _clean_rows(d)
    raw = {r["id"]: r for r in d["raw_asset_register"]}
    used = {a["serial"] for a in d["canonical_assets"]}
    ips = collections.defaultdict(set)
    for a in d["canonical_assets"]:
        if a.get("ip"):
            ips[a["networkSegmentId"]].add(a["ip"])
    seg = {s["id"]: s for s in d["network_segments"]}
    n_serial = n_ip = 0
    for a in d["canonical_assets"]:
        old = a["serial"]
        new = old
        while new in used:
            new = f"SIM-{code}-{rng.randrange(10 ** 6):06d}"
        used.add(new)
        if new != old:
            a["serial"] = new
            _set_payload(raw, rows, a["id"], "시리얼", old, new)
            for rid in rows.get(a["id"], []):
                issue = flagged.get((rid, "시리얼"))
                if issue:
                    issue["expected"] = new
            n_serial += 1
        if a["line"] != "공용" and a.get("ip") and not _blocked(rows, flagged, a["id"], ("IP",)):
            prefix = seg[a["networkSegmentId"]]["cidr"].rsplit(".", 1)[0]
            free = [h for h in range(10, 250) if f"{prefix}.{h}" not in ips[a["networkSegmentId"]]]
            newip = f"{prefix}.{rng.choice(free)}"
            ips[a["networkSegmentId"]].discard(a["ip"])
            ips[a["networkSegmentId"]].add(newip)
            _set_payload(raw, rows, a["id"], "IP", a["ip"], newip)
            a["ip"] = newip
            n_ip += 1
    return n_serial, n_ip


def pick(rng, options):
    """(가중치, 값) 목록에서 하나를 고른다. 가중치 합이 1이 아니어도 된다."""
    total = sum(p for p, _ in options)
    roll = rng.random() * total
    acc = 0.0
    for p, v in options:
        acc += p
        if roll < acc:
            return v
    return options[-1][1]


def retarget(a, new, rows, flagged, raw, sw, tag):
    """자산의 제조사·제품·버전을 바꾸고 대장·설치 목록·오류 표시를 같이 고친다."""
    aid = a["id"]
    old = (a["vendor"], a["product"], a["version"])
    if new == old:
        return False
    a["vendor"], a["product"], a["version"] = new
    a["versionEvidence"] = "unknown_firmware_or_version" if new[2] is None else "synthetic_release_only"
    a["fleetMixV2"] = tag
    for s in sw.get(aid, []):
        if (s["vendor"], s["product"], s["version"]) == old:
            s["vendor"], s["product"], s["version"] = new
    _set_payload(raw, rows, aid, "제조사", old[0], new[0])
    _set_payload(raw, rows, aid, "제품", old[1], new[1])
    _set_payload(raw, rows, aid, "버전", old[2] if old[2] is not None else "", new[2] if new[2] is not None else "")
    _remap_issues(a, new, rows, flagged, raw)
    return True


def apply_line_profiles(d, skip_ids, ctx):
    """라인마다 제조사를 통일한다. 단순 공정(세척·이송)은 LS가 많고 복잡한 공정은 Mitsubishi·Siemens·FANUC가 많다.

    도입 시기가 빠른 라인일수록 오래된 OS를 쓰고, 라인에 새로 추가된 설비 한 대만 가끔 다르다.
    """
    stat = collections.Counter()
    by_site, by_line = {}, {}
    for l in d["lines"]:
        by_site.setdefault(l["siteId"], []).append(l)
    for a in d["canonical_assets"]:
        by_line.setdefault(a["line"], []).append(a)
    for lines in by_site.values():
        for line in lines:
            lr = random.Random(f"{R.SEED}-{d['code']}-{line['id']}")
            year = line["commissionYear"]
            generation = line["generation"]
            
            # 시기 구분 및 OS 설정
            wave = "old" if year < 2022 else ("mid" if year <= 2023 else "new")
            era = "old" if year < 2022 else "new"
            hmi_os = R.LTSC if year < 2024 else (R.WIN11 if lr.random() < 0.7 else R.LTSC)
            vision_os = R.WIN10 if year <= 2022 else (R.LTSC if year == 2023 else R.WIN11)

            # CNC 및 스위치 후보 선정
            cnc_weights = list(R.LINE_CNC_ERA[era])
            if year >= 2024:
                cnc_weights = [(p, v) for p, v in cnc_weights if v != ("Siemens", "SINUMERIK 840D sl", None)]

            plc = pick(lr, R.LINE_PLC)
            prof = {
                "cnc": pick(lr, cnc_weights),
                "robot": pick(lr, R.LINE_ROBOT),
                "plc": pick(lr, R.LS_PLC) if plc == "LS" else plc,
                "inverter": pick(lr, R.LINE_INVERTER),
                "switch": pick(lr, R.LINE_SWITCH_ERA[era]),
                "hmi": hmi_os,
                "vision": vision_os,
            }
            addition = lr.random() < R.LINE_ADDITION_CHANCE
            added = False
            for a in by_line.get(line["id"], []):
                if a["id"] in skip_ids:
                    continue
                a["lineWave"] = wave
                a["lineGeneration"] = generation
                a["lineCommissionYear"] = year
                a["installedYear"] = year

                # 개선 공사(리트로핏) 반영
                if lr.random() < 0.10 and year < 2025:
                    a["installedYear"] = lr.randint(year + 1, 2025)
                    a["retrofitYear"] = a["installedYear"]

                key = R.TYPE_KEY.get(a["assetType"])
                if not key:
                    continue
                target = prof[key]
                if addition and key == "cnc" and not added:
                    target = pick(lr, [(p, v) for p, v in cnc_weights if v != prof["cnc"]])
                    added = True
                    a["installedYear"] = min(2025, year + lr.randint(1, 3))
                    stat["새로 추가된 설비"] += 1
                if retarget(a, target, *ctx, "synthetic_assumption(line_profile)"):
                    stat["라인 프로필 적용"] += 1
    return dict(stat)


def diversify_fleet(d, rng, skip_ids):
    """현실의 혼합 구성. 라인 자산은 라인 프로필로, 공용 자산(사무 PC 등)은 자산 단위로 섞는다.

    버전 미상 PC, 한 번도 확인한 적 없는 자산, 담당 미지정, IP 미할당도 섞는다.
    대장(raw)과 소프트웨어 설치 목록을 같이 고쳐 정답과 어긋나지 않게 하고, 오류가 표시된 필드는 건드리지 않는다.
    """
    assets = d["canonical_assets"]
    rows, flagged = _clean_rows(d)
    raw = {r["id"]: r for r in d["raw_asset_register"]}
    sw = {}
    for s in d["software_installations"]:
        sw.setdefault(s["assetId"], []).append(s)
    ctx = (rows, flagged, raw, sw)
    stat = collections.Counter(apply_line_profiles(d, skip_ids, ctx))
    quality = lambda a: R.GEN_QUALITY.get(a.get("lineWave"), 1.0)
    for a in assets:
        if a["id"] in skip_ids:
            continue
        aid = a["id"]
        if a["line"] == "공용" and a["assetType"] in R.FLEET_MIX:
            roll = rng.random(); acc = 0.0; new = None
            for p, target in R.FLEET_MIX[a["assetType"]]:
                acc += p
                if roll < acc:
                    new = target
                    break
            if new and retarget(a, new, *ctx, "synthetic_assumption(product_mix)"):
                stat["공용 자산 혼합"] += 1
        if a["assetType"] in R.OS_TYPES and rng.random() < R.UNKNOWN_OS_CHANCE:
            if retarget(a, ("Microsoft", "Windows", None), *ctx, "synthetic_assumption(version_unknown)"):
                stat["버전 미상 PC"] += 1
        if a.get("lastVerifiedAt") and not _blocked(rows, flagged, aid, ("확인일",)) and rng.random() < R.NEVER_VERIFIED_CHANCE * quality(a):
            _set_payload(raw, rows, aid, "확인일", a["lastVerifiedAt"], "")
            a["lastVerifiedAt"] = None
            stat["확인한 적 없음"] += 1
        if a.get("ownerId") and not _blocked(rows, flagged, aid, ("담당",)) and rng.random() < R.NO_OWNER_CHANCE * quality(a):
            _set_payload(raw, rows, aid, "담당", a["ownerId"], "")
            a["ownerId"] = None
            stat["담당 미지정"] += 1
        if a.get("ip") and not _blocked(rows, flagged, aid, ("IP",)) and rng.random() < R.NO_IP_CHANCE:
            _set_payload(raw, rows, aid, "IP", a["ip"], "")
            a["ip"] = None
            stat["IP 미할당"] += 1
    return dict(stat)


def add_server_software(d, rng, skip_ids):
    """서버 계층의 OS와 응용 프로그램을 설치 목록에 따로 적는다(수집 계층: OPC 수집·SCADA, 메인 계층: MES·DB·ERP).

    MES DB 서버는 주 제품(SQL Server 2019·2017, Oracle 19c)도 섞는다. 응용 프로그램은 실제 제품이며
    MES 응용 같은 가상 공급사 제품은 기존 설치 항목을 그대로 둔다.
    """
    rows, flagged = _clean_rows(d)
    raw = {r["id"]: r for r in d["raw_asset_register"]}
    sw = {}
    for s in d["software_installations"]:
        sw.setdefault(s["assetId"], []).append(s)
    counts = collections.Counter({k: len(v) for k, v in sw.items()})
    stat = collections.Counter()
    founding = {}
    for l in d["lines"]:
        founding[l["siteId"]] = min(founding.get(l["siteId"], 9999), l["commissionYear"])

    def install(a, product, role):
        counts[a["id"]] += 1
        d["software_installations"].append({
            "id": f"{a['id']}-SW{counts[a['id']]:02d}", "assetId": a["id"], "vendor": product[0], "product": product[1],
            "version": product[2], "role": role, "provenance": "synthetic_installation_assumption_v2"})
        stat[f"설치 항목({role})"] += 1

    for a in d["canonical_assets"]:
        if a["id"] in skip_ids:
            continue
        kind = a["assetType"]
        if kind == "MES DB 서버":
            if retarget(a, pick(rng, R.DB_SERVER), rows, flagged, raw, sw, "synthetic_assumption(db_mix)"):
                stat["DB 제품 혼합"] += 1
            os_choice = R.RHEL8 if a["product"] == "Oracle Database" else pick(rng, [(0.7, R.WS2019), (0.3, R.WS2016)])
            apps = []
        elif kind in R.SERVER_SOFTWARE:
            os_opts, app_opts = R.SERVER_SOFTWARE[kind]
            os_choice = pick(rng, os_opts)
            app = pick(rng, app_opts) if app_opts else None
            apps = [app] if app else []
        else:
            continue
        first = founding.get(a["siteId"], R.FOUNDING_DEFAULT)
        a["installedYear"] = first if rng.random() < 0.7 else rng.randint(min(first + 2, R.LAST_LINE_YEAR), R.LAST_LINE_YEAR)
        install(a, os_choice, "os")
        for app in apps:
            install(a, app, "app")
    return dict(stat)


def pick_by_date(line, year, rng, category, updated_chance=None):
    """빌드 날짜가 있는 계열: OT는 도입 시점 빌드를 대부분 유지(약 25%만 점검 때 갱신), 사무(IT)는 최근 빌드 중심."""
    dates = line.get("candidateDates")
    if not dates:
        return None
    ordered = sorted(dates, key=lambda b: dates[b])
    if category == "OT":
        target = f"{year}-{rng.randint(1, 12):02d}-15"
        base = max((b for b in ordered if dates[b] <= target), key=lambda b: dates[b], default=ordered[0])
        if rng.random() < (R.OT_UPDATED_CHANCE if updated_chance is None else updated_chance):
            later = [b for b in ordered if dates[b] >= dates[base]]
            return rng.choice(later)
        return base
    recent = [b for b in ordered if dates[b] >= R.IT_RECENT_FROM]
    return rng.choice(recent) if recent and rng.random() < R.IT_RECENT_CHANCE else rng.choice(ordered)


def choose_version(pr, wanted_line, year, rng, end_year=None, category="IT"):
    """제품 카탈로그에서 계열(line)과 버전 후보를 고른다. 계열 출시 연도 이전이면 고르지 않는다."""
    if end_year:
        year = min(year, end_year)
    if wanted_line is None:
        options = [l for l in pr["lines"] if (l["ga"] or 0) <= year] or pr["lines"][:1]
        line = options[int(len(options) * (rng.random() ** 0.8))]
    else:
        line = next((l for l in pr["lines"] if l["line"] == wanted_line), None)
        if not line:
            return None
    year = max(year, line["ga"] or 0)
    dated = pick_by_date(line, year, rng, category)
    if dated:
        return line, dated, year
    cands = line["candidates"]
    idx = len(cands) - 1 if rng.random() < 0.2 else int(len(cands) * (rng.random() ** (1.4 if year >= 2023 else 0.8)))
    return line, cands[min(idx, len(cands) - 1)], year


def apply_catalog_installs(d, catalog, research, rng, expected):
    """서버 설치 항목(OS·응용)에 실제 버전을 배정하고 지원 종료일을 붙인다. 설치 항목은 `role`이 있는 것만 다룬다."""
    if not catalog:
        return 0
    products = {p["key"]: p for p in catalog["products"]}
    ends = {(e["match"]["vendor"], e["match"]["product"], e["match"].get("version")): e for e in (research or {}).get("entries", []) if e.get("supportEndDate")}
    assets = {a["id"]: a for a in d["canonical_assets"]}
    done = 0
    for s in d["software_installations"]:
        if not s.get("role"):
            continue
        a = assets[s["assetId"]]
        ref = (s["vendor"], s["product"], s["version"])
        end = ends.get(ref)
        if end:
            s["supportEnd"] = {"date": end["supportEndDate"], "source": end.get("supportEndSource"), "confidence": end.get("supportEndConfidence"), "note": end.get("supportEndNote")}
        key = CATALOG_KEYS.get(ref)
        if not key:
            s["scenario"] = True
            continue
        pr = products[key]
        end_year = int(end["supportEndDate"][:4]) if end else None
        chosen = choose_version(pr, s["version"], a.get("installedYear") or 2022, rng, end_year, a.get("category", "IT"))
        if not chosen:
            continue
        line, version, _ = chosen
        if s["version"] is None:
            s["version"] = version
        s["patchLevel"] = {"label": version, "source": "product_catalog.json", "confidence": "카탈로그 후보(번호만)"}
        s["scenario"] = True
        matches = [] if a.get("lifecycle") == "retired" else [match_advisory(adv, line["line"], version) for adv in pr["advisories"]]
        expected.append({"assetId": a["id"], "softwareId": s["id"], "role": s["role"], "product": key, "line": line["line"],
                         "version": version, "lifecycle": a.get("lifecycle"), "matches": matches})
        done += 1
    return done


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


def update_summary(d, as_of, hetero_ids, research_hits, extra_ids, catalog_hits=0, fleet_stat=None):
    s = d["summary"]; q = d["quality_truth"]["issues"]
    s["assets"] = len(d["canonical_assets"])
    s["assetTypes"] = dict(collections.Counter(x["assetType"] for x in d["canonical_assets"]))
    s["equipment"] = len(d["equipment"]); s["cncMachines"] = sum(1 for a in d["canonical_assets"] if a["assetType"] == "CNC 컨트롤러")
    s["lines"] = len(d["lines"]); s["rawRows"] = len(d["raw_asset_register"]); s["issues"] = len(q)
    s["issueTypes"] = dict(sorted(collections.Counter(i["issueType"] for i in q).items()))
    d["schemaVersion"] = "2.0-draft"
    d["v2"] = {"generator": "generate_v2.py", "seed": R.SEED, "asOfProgress": as_of, "heterogeneityAssets": hetero_ids,
               "researchedAssets": research_hits, "fleetMix": fleet_stat, "catalogAssets": catalog_hits, "addedAssetIds": extra_ids, "note": "원본 대비 파생 데이터. 변형 값은 시험용 가정이며 실제 회사 자료가 아니다."}


def raw_matches_truth(d):
    assets = {a["id"]: a for a in d["canonical_assets"]}
    flagged_rows = {i["rowId"] for i in d["quality_truth"]["issues"]}
    for r in d["raw_asset_register"]:
        a = assets[d["quality_truth"]["row_to_asset"][r["id"]]]
        if r["id"].endswith("-DUP") or r["id"] in flagged_rows:
            continue
        for field, key in (("제조사", "vendor"), ("제품", "product")):
            if field not in r["payload"]:
                continue
            if r["payload"][field].strip().lower() != a[key].strip().lower():   # 공백·대소문자 변형은 원본의 의도된 잡음
                return False
    return True


def growth_ok(d):
    by_site = {}
    for l in d["lines"]:
        by_site.setdefault(l["siteId"], []).append(l)
    for lines in by_site.values():
        years = [l["commissionYear"] for l in lines]
        founding = [l for l in lines if l["generation"] == 0]
        if years != sorted(years) or not 2 <= len(founding) <= 3 or years[-1] > R.LAST_LINE_YEAR:
            return False
    year_of = {l["id"]: l["commissionYear"] for l in d["lines"]}
    return all(a["installedYear"] >= year_of[a["line"]] for a in d["canonical_assets"] if a["line"] in year_of and a.get("lineWave"))


def line_types_ok(d):
    cnc = collections.Counter(a["line"] for a in d["canonical_assets"] if a["assetType"] == "CNC 컨트롤러")
    return all((cnc[l["id"]] >= 6) if l["lineType"] == "가공" else (cnc[l["id"]] == 0) for l in d["lines"])


def line_vendor_ok(d):
    kinds = {}
    for a in d["canonical_assets"]:
        if a["assetType"] == "CNC 컨트롤러":
            kinds.setdefault(a["line"], set()).add(a["product"])
    return all(len(v) <= 2 for v in kinds.values())


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
        "대장 제조사·제품 일치(오류 표시 없는 행)": raw_matches_truth(d),
        "라인 유형별 구성(세척·조립에 CNC 없음, 가공 CNC 6대 이상)": line_types_ok(d),
        "라인 성장(최초 2~3개 라인, 개설 연도 비감소, 설치 연도가 개설 연도 이후)": growth_ok(d),
        "라인당 CNC 제조사 2종 이하": line_vendor_ok(d),
        "기간 하루 이상": max(dt.datetime.fromisoformat(o["simulatedTimestamp"]) for o in d["machine_observations"]) - base > dt.timedelta(hours=24),
    }
    return checks


def build(code, src, out, research, catalog=None):
    d = json.loads((src / f"{code.lower()}_factory.json").read_text(encoding="utf-8"))
    original_obs = copy.deepcopy([o["original"] for o in d["machine_observations"]])
    rng = random.Random(f"{R.SEED}-{code}")
    restructure_stat = restructure_lines(d)
    vary_attributes(d["canonical_assets"], rng)
    add_exposure_edr_reboot(d["canonical_assets"], d["lines"], rng)
    hetero_ids = apply_heterogeneity(d, rng)
    fleet_stat = diversify_fleet(d, rng, set(hetero_ids))
    assign_process_attributes(d, rng)
    fleet_stat.update(restructure_stat)
    fleet_stat["담당 분리"] = assign_owners(d, rng)
    fleet_stat["시리얼·IP 불규칙화"] = randomize_identifiers(d, rng)
    fleet_stat.update(add_server_software(d, rng, set(hetero_ids)))
    d["quality_truth"]["issues"] = [i for i in d["quality_truth"]["issues"] if not i.get("_drop")]
    hits = apply_research(d["canonical_assets"], d["software_installations"], research, rng)
    extra_ids = add_extra_assets(d, rng)
    diversify_flows(d, rng)
    fleet_stat["라인 통신 추가"] = add_line_flows(d, rng)
    expected = []
    catalog_hits = apply_catalog(d["canonical_assets"], catalog, research, rng, expected)
    catalog_hits += apply_catalog_installs(d, catalog, research, rng, expected)
    fix_lines(d)
    as_of = rebuild_mes(d, rng)
    vary_reported(d, rng); reassign_sources(d, rng); add_cross_file_conflicts(d, rng); renumber(d)
    update_summary(d, as_of, hetero_ids, hits, extra_ids, catalog_hits, fleet_stat)
    checks = validate(d); checks["AI4I 원본값 보존"] = original_obs == [o["original"] for o in d["machine_observations"]]
    note = ("정답지(QA 비교용): 자산의 제품·버전을 공개 공지와 비교한 기대 결과. 앱이 읽는 데이터가 아니다. "
            "수집기가 새 공지를 받았을 때 낸 결과가 이것과 맞는지 확인하는 데 쓴다. EPSS는 시험용 값(synthetic)이다.")
    (out / f"{code.lower()}_expected_matches.json").write_text(
        json.dumps({"note": note, "scenario": True, "company": code, "items": expected}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (out / f"{code.lower()}_factory_v2.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return checks, hits


def main(src, out, research_path=None, catalog_path=None):
    src, out = pathlib.Path(src), pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    research = json.loads(pathlib.Path(research_path).read_text(encoding="utf-8")) if research_path and pathlib.Path(research_path).exists() else None
    catalog = json.loads(pathlib.Path(catalog_path).read_text(encoding="utf-8")) if catalog_path and pathlib.Path(catalog_path).exists() else None
    for code in ("VMA", "VMB", "VMC"):
        checks, hits = build(code, src, out, research, catalog)
        print(code, "조사값 적용 자산", hits, "|", "통과" if all(checks.values()) else "실패", {k: v for k, v in checks.items() if not v} or "")


if __name__ == "__main__":
    main(*sys.argv[1:5])
