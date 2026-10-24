"""생성 결과(out/*_v2.json)에서 수치를 세어 변경 내역 문서의 자동 구간을 다시 쓴다.

사용: python render_report.py <out 폴더> <07 문서 경로>
문서의 `<!-- AUTO:START -->` ~ `<!-- AUTO:END -->` 사이만 바꾼다.
"""
import collections
import json
import pathlib
import sys

START, END = "<!-- AUTO:START -->", "<!-- AUTO:END -->"


def stats(d, exp):
    a = d["canonical_assets"]
    cat = exp["items"]
    status = collections.Counter(m["status"] for x in cat for m in x["matches"])
    ports = collections.Counter(f["port"] for f in d["application_flows"])
    return {
        "자산": len(a), "버전 배정 자산": len(cat), "대장 행": len(d["raw_asset_register"]),
        "작업지시": len(d["mes_work_orders"]),
        "중요도 high/mid/low": "/".join(str(sum(1 for x in a if x["criticality"] == k)) for k in ("high", "mid", "low")),
        "되돌리기 가능/불가": f'{sum(1 for x in a if x["rollbackPossible"])}/{sum(1 for x in a if not x["rollbackPossible"])}',
        "노출 장비(remote·dmz·perimeter)": sum(1 for x in a if x.get("exposure") not in (None, "internal")),
        "통신 4840(OPC UA)": f'{ports[4840]}/{len(d["application_flows"])}',
        "통신 102·5007": f'{ports[102]}·{ports[5007]}',
        "제품 종류(제조사·제품 조합)": len({(x["vendor"], x["product"]) for x in a}),
        "버전·펌웨어 미상": sum(1 for x in a if x.get("versionEvidence") == "unknown_firmware_or_version"),
        "IP 미할당": sum(1 for x in a if not x.get("ip")),
        "담당 미지정": sum(1 for x in a if not x.get("ownerId")),
        "한 번도 확인한 적 없음": sum(1 for x in a if not x.get("lastVerifiedAt")),
        "지원 종료 자산": sum(1 for x in a if x.get("supportStatus") == "ended"),
        "정답지의 판정 분포": dict(sorted(status.items())),
    }


def render(out_dir):
    load = lambda name: json.loads((out_dir / name).read_text(encoding="utf-8"))
    rows = {c: stats(load(f"{c.lower()}_factory_v2.json"), load(f"{c.lower()}_expected_matches.json")) for c in ("VMA", "VMB", "VMC")}
    keys = list(rows["VMA"])
    lines = ["| 항목 | VMA | VMB | VMC |", "|---|---|---|---|"]
    for k in keys:
        lines.append(f"| {k} | " + " | ".join(str(rows[c][k]) for c in rows) + " |")
    return "\n".join(lines)


def main(out_dir, doc):
    out_dir, doc = pathlib.Path(out_dir), pathlib.Path(doc)
    text = doc.read_text(encoding="utf-8")
    i, j = text.index(START) + len(START), text.index(END)
    doc.write_text(text[:i] + "\n" + render(out_dir) + "\n" + text[j:], encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:3])
