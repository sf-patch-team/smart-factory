"""BPI Challenge 2013(Volvo IT 장애 처리 로그)에서 **집계 통계만** 뽑는다.

- 입력: BPI_Challenge_2013_incidents.xes.gz (비공식 재배포본, 원본과 해시 동일성 미확인). 저장소에 올리지 않는다.
- 출력: 통계 JSON. 담당자 이름·국가·조직·제품 번호 같은 개별 값은 넣지 않는다.
- 사용: python -I scripts/bpi/analyze_bpi2013.py <xes.gz 경로> <출력 json>
출처: Volvo IT Belgium 장애 관리 시스템 로그, BPI Challenge 2013 (W. Steeman).
"""
import gzip
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9, 0.99)


def quantiles(values):
    values = sorted(values)
    if len(values) < 2:
        return {}
    out = {f"p{int(q * 100)}": round(values[min(len(values) - 1, int(q * len(values)))], 2) for q in QUANTILES}
    out["n"] = len(values)
    out["max"] = round(values[-1], 2)
    return out


def share(counter: Counter, top=None):
    total = sum(counter.values()) or 1
    return {key: round(count / total, 4) for key, count in counter.most_common(top)}


def read_cases(path: Path):
    with gzip.open(path, "rb") as handle:
        for _, element in ET.iterparse(handle, events=("end",)):
            if element.tag.split("}")[-1] != "trace":
                continue
            events = []
            for child in element:
                if child.tag.split("}")[-1] != "event":
                    continue
                events.append({c.attrib.get("key"): c.attrib.get("value") for c in child})
            element.clear()
            yield events


def main(source: str, output: str) -> None:
    impact, steps, transitions = Counter(), Counter(), Counter()
    durations_days, event_counts, group_counts = [], [], []
    cases = 0
    for events in read_cases(Path(source)):
        if not events:
            continue
        cases += 1
        impact[events[0].get("impact", "")] += 1
        event_counts.append(len(events))
        group_counts.append(len({e.get("org:group") for e in events}))
        for event in events:
            steps[event.get("concept:name", "")] += 1
        for before, after in zip(events, events[1:]):
            transitions[f"{before.get('concept:name')} → {after.get('concept:name')}"] += 1
        first = datetime.fromisoformat(events[0]["time:timestamp"])
        last = datetime.fromisoformat(events[-1]["time:timestamp"])
        durations_days.append((last - first).total_seconds() / 86400)
    result = {
        "source": "BPI Challenge 2013 incidents (Volvo IT), 비공식 재배포본 기준. 집계 통계만 포함",
        "cases": cases,
        "impact_first_event": share(impact),
        "steps": share(steps, 8),
        "top_transitions": share(transitions, 8),
        "events_per_case": quantiles(event_counts),
        "groups_per_case": quantiles(group_counts),
        "case_duration_days": quantiles(durations_days),
    }
    Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", output)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
