"""BPI Challenge 2014(Rabobank IT 서비스 관리 기록)에서 **집계 통계만** 뽑는다.

- 입력: BPI-2014 폴더(Detail Change.csv, Detail Incident.csv, Detail Interaction.csv). 원본은 저장소에 올리지 않는다.
- 출력: 통계 JSON 한 개. CI 이름·변경/장애 번호 같은 개별 식별 값은 넣지 않는다(마지막에 검사한다).
- 사용: python -I scripts/bpi/analyze_bpi.py <BPI-2014 폴더> <출력 json>
출처: Rabobank Group ICT, BPI Challenge 2014 (B.F. van Dongen). 아래 통계는 이 데이터에서 계산한 값이다.
"""
import csv
import json
import re
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

csv.field_size_limit(10**7)
QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9, 0.99)
ID_PATTERN = re.compile(r"\b(IM|SD|C|HMD|SBA|SUB|WBS)\d{4,}\b")


def read_rows(path: Path):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            yield {key: (value or "").strip() for key, value in row.items() if key}


def parse_time(text: str):
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def to_float(text: str):
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def quantiles(values):
    values = sorted(v for v in values if v is not None)
    if len(values) < 2:
        return {}
    cuts = {q: values[min(len(values) - 1, int(q * len(values)))] for q in QUANTILES}
    return {f"p{int(q * 100)}": round(v, 2) for q, v in cuts.items()} | {
        "mean": round(statistics.fmean(values), 2), "max": round(values[-1], 2), "n": len(values)}


def share(counter: Counter, top=None):
    total = sum(counter.values()) or 1
    items = counter.most_common(top)
    return {key or "(없음)": round(count / total, 4) for key, count in items}


def analyze_changes(path: Path):
    risk, emergency, cab, ctype, ci_type = Counter(), Counter(), Counter(), Counter(), Counter()
    sched_down, actual_dur, start_delay, rel_inc = [], [], [], Counter()
    related_by_risk: dict[str, list[int]] = {}
    total = with_downtime = 0
    per_ci: Counter = Counter()
    for row in read_rows(path):
        total += 1
        per_ci[row.get("CI Name (aff)", "")] += 1
        level = row.get("Risk Assessment", "")
        risk[level] += 1
        emergency[row.get("Emergency Change", "")] += 1
        cab[row.get("CAB-approval needed", "")] += 1
        ctype[row.get("Change Type", "")] += 1
        ci_type[row.get("CI Type (aff)", "")] += 1
        down_start, down_end = parse_time(row.get("Scheduled Downtime Start", "")), parse_time(row.get("Scheduled Downtime End", ""))
        if down_start and down_end and down_end >= down_start:
            with_downtime += 1
            sched_down.append((down_end - down_start).total_seconds() / 60)
        start, end = parse_time(row.get("Actual Start", "")), parse_time(row.get("Actual End", ""))
        if start and end and end >= start:
            actual_dur.append((end - start).total_seconds() / 60)
        planned = parse_time(row.get("Planned Start", ""))
        if planned and start:
            start_delay.append((start - planned).total_seconds() / 86400)
        incidents = int(to_float(row.get("# Related Incidents", "")) or 0)
        related_by_risk.setdefault(level, []).append(incidents)
        rel_inc["있음" if incidents > 0 else "없음"] += 1
    by_risk = {k: {"changes": len(v), "share_with_incident": round(sum(1 for x in v if x > 0) / len(v), 4)}
               for k, v in related_by_risk.items()}
    return {
        "changes": total, "distinct_ci": len(per_ci),
        "changes_per_ci": quantiles(list(per_ci.values())),
        "risk_assessment": share(risk), "emergency": share(emergency), "cab_needed": share(cab),
        "change_type_top": share(ctype, 8), "ci_type": share(ci_type),
        "share_with_scheduled_downtime": round(with_downtime / total, 4),
        "scheduled_downtime_minutes": quantiles(sched_down),
        "actual_duration_minutes": quantiles(actual_dur),
        "start_delay_days_vs_plan": quantiles(start_delay),
        "share_with_related_incident": share(rel_inc),
        "related_incident_share_by_risk": by_risk,
    }


def analyze_incidents(path: Path):
    impact, urgency, priority, ci_type, ci_subtype, status, closure = (Counter() for _ in range(7))
    per_ci: Counter = Counter()
    handle_hours, reassign, resolve_days = [], [], []
    type_cis: dict[str, set] = {}
    first_open = last_open = None
    total = 0
    for row in read_rows(path):
        total += 1
        type_cis.setdefault(row.get("CI Type (aff)", ""), set()).add(row.get("CI Name (aff)", ""))
        opened_at = parse_time(row.get("Open Time", ""))
        if opened_at:
            first_open = min(first_open or opened_at, opened_at)
            last_open = max(last_open or opened_at, opened_at)
        impact[row.get("Impact", "")] += 1
        urgency[row.get("Urgency", "")] += 1
        priority[row.get("Priority", "")] += 1
        ci_type[row.get("CI Type (aff)", "")] += 1
        ci_subtype[row.get("CI Subtype (aff)", "")] += 1
        status[row.get("Status", "")] += 1
        closure[row.get("Closure Code", "")] += 1
        per_ci[row.get("CI Name (aff)", "")] += 1
        handle_hours.append(to_float(row.get("Handle Time (Hours)", "")))
        reassign.append(to_float(row.get("# Reassignments", "")))
        opened, resolved = parse_time(row.get("Open Time", "")), parse_time(row.get("Resolved Time", ""))
        if opened and resolved and resolved >= opened:
            resolve_days.append((resolved - opened).total_seconds() / 86400)
    ci_type_counts = ci_type
    return {
        "incidents": total, "distinct_ci": len(per_ci),
        "period_days": (last_open - first_open).days if first_open and last_open else None,
        "mean_incidents_per_ci_by_type": {
            (key or "(없음)"): round(ci_type_counts[key] / max(1, len(cis)), 2) for key, cis in type_cis.items()},
        "impact": share(impact), "urgency": share(urgency), "priority": share(priority),
        "ci_type": share(ci_type), "ci_subtype_top": share(ci_subtype, 12), "status": share(status),
        "closure_code_top": share(closure, 8),
        "incidents_per_ci": quantiles(list(per_ci.values())),
        "handle_time_hours": quantiles(handle_hours),
        "reassignments": quantiles(reassign),
        "open_to_resolved_days": quantiles(resolve_days),
    }, per_ci


def analyze_interactions(path: Path):
    total, first_call = 0, Counter()
    handle = []
    ci_type = Counter()
    for row in read_rows(path):
        total += 1
        first_call[row.get("First Call Resolution", "")] += 1
        ci_type[row.get("CI Type (aff)", "")] += 1
        handle.append(to_float(row.get("Handle Time (secs)", "")))
    return {"interactions": total, "first_call_resolution": share(first_call),
            "ci_type": share(ci_type), "handle_time_secs": quantiles(handle)}


def forbid_identifiers(data) -> None:
    text = json.dumps(data, ensure_ascii=False)
    if ID_PATTERN.search(text):
        raise SystemExit("개별 식별 값이 통계에 섞였다: 출력하지 않는다")


def main(folder: str, output: str) -> None:
    base = Path(folder)
    incident_stats, per_ci = analyze_incidents(base / "Detail Incident.csv")
    result = {
        "source": "BPI Challenge 2014 (Rabobank Group ICT), B.F. van Dongen. 집계 통계만 포함",
        "changes": analyze_changes(base / "Detail Change.csv"),
        "incidents": incident_stats,
        "interactions": analyze_interactions(base / "Detail Interaction.csv"),
    }
    forbid_identifiers(result)
    Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", output)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
