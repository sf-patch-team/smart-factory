# 데이터 출처 카드

> 작성 2026-10-22 · 연결: [PRD](PRD.md) · [ERD](db/erd.md) · [00 결정 기록](00-리서치-주제결정.md)
> 과제 조건: 실제 회사 자료·개인정보 금지(가상 자료만). 아래 "BPI 통계"는 실제 회사 기록에서 **집계한 분포**만 쓰고, 개별 행·이름·번호는 쓰지 않는다.

## 1. 한눈에
| 데이터 | 역할 | 성격 | 저장소에 있는 것 | 확인 정도 |
|---|---|---|---|---|
| CISA KEV | 실시간 취약점(기준) | 공식 공개, CC0 | 가져오는 코드(`parseKev`), 시험용 가짜 12개 | 직접 내려받아 확인(1,754개, 2026.10.21판) |
| 가상 공장 자산 115개 | 회원 입력 데이터 | **설계한 가상 데이터** | `seed/assets.ts` | 시험 29건으로 구조 확인 |
| BPI 2014 통계 | 장애·변경 이력의 분포 | 실제 회사 기록의 **집계** | `seed/data/bpi2014-stats.json`(6.5KB) | 파일을 직접 열어 계산 |
| BPI 2013 통계 | 접수→처리 흐름 분포 | 실제 회사 기록의 **집계** | `seed/data/bpi2013-stats.json` | 비공식 재배포본, 해시 미확인 |
| 가상 과거 이력 | 자산별 장애·변경 기록 | 위 통계로 **새로 생성** | `seed/assetHistory.ts`(고정 난수) | 시험 9건 |

## 2. CISA KEV
- 출처: https://www.cisa.gov/known-exploited-vulnerabilities-catalog · 미러 https://github.com/cisagov/kev-data (CC0)
- 확인(2026-10-22): 항목 1,754개, 열 `cveID, vendorProject, product, vulnerabilityName, dateAdded, shortDescription, requiredAction, dueDate, knownRansomwareCampaignUse, forensicTriage, notes, cwes`
- 한계: **버전 정보가 없다**. 제품명이 "Windows"처럼 넓은 항목이 많아 같은 OS를 쓰는 자산에 후보가 수백 건씩 붙는다(115개 자산 × 실제 KEV = 후보 6,780건, 그중 Microsoft 6,493건). → 같은 제품·버전 자산 묶음 확인과 상위 N건 표시가 필요하다(결정 대기).

## 3. BPI Challenge 2014 (Rabobank Group ICT)
- 내용: IT 서비스 관리 도구 기록. 이번에 쓴 파일 3개: 변경(30,275건), 장애(46,809건), 문의(147,004건). 장애 기간 약 785일.
- 입수: https://files.fluxicon.com/Datasets/BPIC/BPI-Challenge-2014.zip (사용자 PC에서 받은 사본, 2026-10-22)
- 원출처·인용: B.F. van Dongen, *BPI Challenge 2014*, 4TU.ResearchData. 이용 조건은 4TU 일반 이용 약관(검색 결과로 확인, **약관 원문은 직접 읽지 못함**) — 출처 표기를 한다.
- 재현: `python -I scripts/bpi/analyze_bpi.py <BPI-2014 폴더> src/infrastructure/seed/data/bpi2014-stats.json` (원본은 저장소에 올리지 않는다)
- 뽑은 통계(요약)
  | 항목 | 값 |
  |---|---|
  | 변경 위험도 | 일반 변경 93.96% · 업무 변경 5.67% · 대형 업무 변경 0.37% |
  | 긴급 변경 | 0.3% · CAB 승인 필요 6.6% |
  | 계획된 중단이 있는 변경 | 2.5%, 중단 시간 중앙값 240분(p90 570분) |
  | 변경에 연결된 장애가 있었던 비율 | 전체 6.4% · 일반 5.3% · 업무 변경 24.9% (※ 원인이라는 뜻이 아님) |
  | 장애 처리 시간(시간) | 중앙값 3.9 · p90 48 · p99 395 |
  | 접수→해결(일) | 중앙값 0.78 · p90 11 |
  | 재배정 횟수 | 중앙값 0 · p90 3 |
  | CI당 장애 수 | 중앙값 1 · p90 9 · p99 330(꼬리가 길다) |
  | CI 종류별 평균 장애 수 | 응용프로그램 64 · 하위 응용 79 · 데이터베이스 21 · 컴퓨터 1.8 · 네트워크 장비 1.1 |
- 한계: 은행 IT 기록이라 **공장 설비(PLC 등) 기록이 아니다**. 영향도·우선순위 숫자(1~5)의 의미는 설명서(`Quick reference`)로 확인하지 못해 사용하지 않았다.

## 4. BPI Challenge 2013 (Volvo IT Belgium)
- 내용: 장애 처리 이벤트 로그(7,554건 사례, 65,533 이벤트).
- 입수: 원 서버(4TU)에 연결되지 않아 **비공식 재배포본**(github.com/DogukanDG/bpic2013-to-simod-csv)을 사용했다. 원본과 해시 동일성은 확인하지 못했다. 저장소 코드의 MIT 라이선스를 데이터에 적용하지 않는다.
- 원출처·인용: W. Steeman, *BPI Challenge 2013, incidents*, 4TU.ResearchData, DOI 10.4121/uuid:500573e6-accc-4b0c-9576-aa5468b10cee
- 개인정보 주의: 원본에 **담당자 이름·국가·조직 코드**가 있다. 통계에는 넣지 않았다(스크립트가 집계만 출력, 검사함).
- 재현: `python -I scripts/bpi/analyze_bpi2013.py <xes.gz> src/infrastructure/seed/data/bpi2013-stats.json`
- 뽑은 통계: 첫 영향도 중간 53.6% · 낮음 43.0% · 높음 3.5% · 사례당 이벤트 중앙값 6 · 사례당 처리 그룹 중앙값 2 · 사례 처리 기간 중앙값 7.6일(p90 22.6일). 단계는 Accepted 61% · Completed 21% · Queued 18%.

## 5. 가상 공장 자산 115개 (설계 데이터)
- 구조: 구역 9 → 라인 17 → 자산. 프레스동·조립동·도장동·포장·물류동·품질검사동·수전·유틸리티동·중앙 제어실·데이터센터·경계망. OT 91 · IT 24.
- BPI가 아니라 **공장 계층 구조로 직접 설계**했다. 벤더·제품은 KEV와 맞는 것(Microsoft, Siemens, Rockwell, Cisco, Fortinet, Palo Alto, Ivanti, SonicWall, VMware)과 안 맞는 것(Moxa, Mitsubishi, Advantech, Beckhoff, Schneider Modicon, Veeam)을 섞었다.
- 패치 제약(벤더 승인 필요·가동 중 불가·점검 창)은 OT 자산에 우선 부여했다(우리 가정).

## 6. 가상 과거 이력 (BPI 통계로 생성)
- 생성: `buildAssetHistory(assets, today, seed)` — 고정 난수라서 같은 입력이면 같은 결과.
- 대응 규칙(우리 가정): 자산 종류를 BPI의 CI 유형에 이렇게 대응했다.
  | 우리 자산 | 묶음 | BPI 대응 |
  |---|---|---|
  | HMI PC, 엔지니어링 PC, 서버 | computer | computer |
  | 스위치, 방화벽, 라우터, VPN, 게이트웨이 | network | networkcomponents |
  | 공정 소프트웨어 | application | application |
  | PLC, 통신 모듈, 모션·전력 컨트롤러 | device | **대응 없음 → hardware 수치를 임시 사용** |
- 장애 수: BPI의 "CI당 장애 수" 분포에서 뽑아 연 단위로 환산하고(785일 → 365일) 유형별 배율(0.2~3배)을 곱한다. 상한 연 25건.
- 변경 수: BPI의 "CI당 변경 수" 분포에서 뽑는다(기간은 장애와 같다고 가정). 상한 연 20건.
- 점검 창이 있는 자산의 변경에는 계획된 중단 시간을 반드시 둔다(우리 가정).
- 결과 예(2026-10-22 기준, seed 2026): 장애 174건 · 변경 161건, 장애가 있는 자산 22/115, 변경 위험도는 일반 94%(151건)·업무 6%(10건).

## 7. 발표·문서에 쓸 문장
"장애·변경 이력은 공개된 연구용 IT 서비스 기록(BPI Challenge 2013·2014)의 **통계 분포만 참고해 새로 생성한 가상 데이터**입니다. 원본 기록과 이름은 사용하지 않았고, 공장 설비 기록이 아니라서 대응 규칙은 팀의 가정입니다."

## 8. 아직 비어 있는 것·결정 대기
- 가상 과거 이력을 **앱 화면에 보여 주려면** DB 표(`asset_events`)와 화면이 필요하다. 아직 만들지 않았고 승인 대기(ERD 변경).
- 이력을 우선순위 점수에 반영할지(spec 범위 밖, "가능하면").
- 4TU 원본 파일로 BPI 2013의 해시를 맞춰 보지 못했다.
