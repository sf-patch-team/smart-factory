# smart-factory — 자산 취약점 패치 관리

스마트팩토리의 설비·IT 자산과 CISA KEV를 대조해 취약점 후보를 확인하고,
패치 요청 → 승인 → 처리 → 검증 → 완료 이력을 관리하는 팀 프로젝트입니다.
호환성과 해당 여부는 사람이 확인하며 실제 장비에 패치를 실행하지 않습니다.

## 실행

```bash
npm install
```

`.env.example`을 `.env.local`로 복사하고 필요한 값을 직접 설정합니다.
실제 키·비밀번호는 저장소에 올리지 않습니다.

```bash
npm run dev
npm test
npm run typecheck
```

Next.js·React·TypeScript·Supabase를 사용합니다. 정확한 설치 버전은 package-lock.json이 기준입니다.
현재 화면·로그인·원격 DB 연결의 완성 여부는 각각 검증해야 합니다.

## 데이터셋

[가상 대형 제조공장 3개사 데이터](docs/datasets/manufacturing-mes-20261022/README.md)를 제공합니다.
같은 자동차부품 금속가공 업종이며 MES·SCADA·ERP 연계·자산·네트워크 구성을 포함합니다.

| 가상 회사 | 공장 | 라인 | CNC | 관리 자산 | 오염 대장 행 |
|---|---:|---:|---:|---:|---:|
| 한결정밀 VMA | 1 | 12 | 60 | 387 | 417 |
| 새온모빌리티 VMB | 1 | 16 | 96 | 556 | 599 |
| 이음오토파츠 VMC | 2 | 24 | 144 | 864 | 931 |

실제 기업은 공개 제품 분야를 참고하는 연결 정보일 뿐입니다.
설비·인원·망·MES·오류·취약점 정보는 해당 기업의 실제 자료가 아닙니다.
AI4I 합성 데이터 10,000행을 회사별로 나누고 가상 생산 관계를 추가했습니다.
출처·CC BY 4.0 이용 조건·변형 내용은 데이터셋 설명서와 JSON의 sources에 명시했습니다.
Bosch 자료는 공정 구조 설명만 참고했으며 원본 수치 데이터는 포함하지 않았습니다.

자산 JSON은 아직 앱·DB에 적재하지 않았습니다. 기존 시드·SQL은 별개입니다.
quality_truth는 QA 정답표이며 일반 사용자 업로드 입력으로 쓰지 않습니다.
SIM-MES 등 가상 제품을 실제 CVE와 직접 연결하지 않습니다.
AI4I 기계 고장은 보안 취약점이나 패치 실패의 증거가 아닙니다.

## 핵심 문서

| 문서 | 내용 |
|---|---|
| [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) | 도구 진입점·공통 작업 규칙 |
| [PRD](docs/PRD.md) | 요구사항·핵심 여정·예외·설계 결정 |
| [ERD](docs/db/erd.md) | DB 구조·접근 규칙, 실제 변경은 SQL 마이그레이션 기준 |
| [인수인계](docs/인수인계.md) | 현재 작업·검증·다음 할 일 |
| [데이터셋 설명](docs/datasets/manufacturing-mes-20261022/README.md) | 출처·구조·가상 데이터 범위 |

상세 기획·리서치·분담은 팀 협의로 관리하며 저장소에는 핵심 문서 7개만 둡니다.
각자 브랜치에서 작업하고 PR → 리뷰 → 머지합니다. main에 직접 push하지 않습니다.

## KEV·EPSS 변경 수집 프로그램

FR-05·FR-24를 위한 독립 파일 수집기입니다. Python 3.10 이상과 기본 라이브러리만 사용합니다.
KEV·EPSS를 받는 데 회원가입·로그인·API 키는 필요하지 않습니다.

```bash
python scripts/sync_vulnerability_feeds.py
python scripts/sync_vulnerability_feeds.py --watch
python -m unittest discover -s tests -p "test_feed_sync.py" -v
```

한 번 실행하면 두 데이터를 확인하고 종료합니다. `--watch`는 프로세스가 실행되는 동안
KEV를 기본 900초마다, EPSS를 86400초마다 확인합니다. 변경 알림을 직접 받는 방식은 아닙니다.
`--kev-seconds`, `--epss-seconds`로 간격을 바꾸며 각각 최소 60초입니다. Ctrl+C로 종료합니다.
PC 종료·프로그램 종료 뒤에는 확인하지 않습니다. 운영 서버의 예약 실행 등록은 별도 작업입니다.

저장 위치는 기본 `scratch/vulnerability-feeds/`이며 Git에서 제외됩니다. `--output`으로 변경할 수 있습니다.
`current.json`의 각 소스 `file`이 검증된 최신 파일이고, 경로는 저장 폴더를 기준으로 해석합니다.
소스별 `checked_at`·`fetched_at`·`source_date`·해시·모델/카탈로그 버전을 구분합니다.
이전 원본은 해시별로 보존합니다. CISA 본원 장애 시 공식 GitHub 미러를 사용합니다.

성공 기준: FS-1 정상 두 형식 저장, FS-2 동일/304 중복 방지, FS-3 오류 시 이전 정상본 유지,
FS-4 과거 자료·20% 초과 수량 감소 차단, FS-5 중복 실행 차단, FS-6 소스별 확인 주기와 날짜 구분.
소스별로 독립 반영하며 하나가 실패해도 다른 소스를 확인합니다. 전체 성공 시 종료 코드 0, 실패 시 1입니다.
네트워크 오류는 제한 재시도하며, 20% 초과 감소는 원본 변경을 확인한 뒤 수동 검토해야 합니다.
이미 수신한 원본·승인·완료 기록을 삭제하지 않습니다. 이 수집기는 앱·Supabase·패치 요청을 수정하지 않습니다.

공식 근거: [CISA KEV](https://github.com/cisagov/kev-data),
[FIRST 일일 CSV 안내](https://www.first.org/epss/data), [EPSS API](https://api.first.org/epss/).
