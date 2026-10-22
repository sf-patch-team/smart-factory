# smart-factory — 자산 취약점 패치 관리

공장 설비와 IT 자산 중 **지금 위험한 취약점**을 찾아 패치를 요청·승인·기록하는 웹앱입니다. (LS 클래스 프로젝트 2, 마감 2026-10-27)
미국 CISA의 [KEV](https://github.com/cisagov/kev-data)(실제 악용이 확인된 취약점 목록)와 팀이 만든 **가상 자산**을 맞춰 보고, 점수 순으로 보여 줍니다.

> 모든 자료는 가상입니다. 실제 회사 자료·실명·연락처는 쓰지 않습니다.

## 시작하기
```bash
npm install
cp .env.example .env.local   # 값은 직접 채웁니다(저장소에 올리지 않음)
npm run dev                  # http://localhost:3000
npm test                     # 규칙 시험(Vitest)
```
- `.env.local`에 Supabase 주소·키를 넣어야 로그인·DB가 동작합니다. 키는 **절대 저장소·채팅에 올리지 않습니다**.
- 값이 없어도 규칙 시험(`npm test`)과 화면 뼈대는 확인할 수 있습니다.

## 개발용 데이터 (DB에 이미 들어 있음)
Supabase `smart-factory`에 가상 사용자 4명(담당자 3 · 관리자 1), 가상 자산 115개, KEV 1,754개, 매칭 후보 6,780건, 가상 이력 335건이 들어 있습니다.
- 로그인용 가상 계정: `member1~3@example.com`(담당자), `admin@example.com`(관리자). 비밀번호는 `.env.local`의 `SEED_USER_PASSWORD`이고, **프로젝트 소유자(A)가 개인적으로 전달**합니다.
- 다시 채우려면(소유자만, 서비스 키 필요): `npx tsx scripts/seed.ts` — 여러 번 실행해도 같은 결과가 됩니다.

## 문서
| 문서 | 내용 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | 프로젝트 규칙 |
| [Intent.md](Intent.md) · [spec.md](spec.md) · [plan.md](plan.md) | 작업 의도 · 무엇을 · 어떻게 |
| [GLOSSARY.md](GLOSSARY.md) | 용어집 |
| [docs/](docs/) | 리서치, Mom Test, IA, UJ, PRD, ERD, ADR, 디자인 |

## 협업 규칙
각자 브랜치에서 맡은 조각만 만들고 **PR → 리뷰 → 머지**합니다. `main`에 직접 올리지 않습니다.

## 문제가 생기면
- 로그인이 안 됨: `.env.local`의 Supabase 값 확인
- 위험 목록이 비어 있음: 관리자 화면 "데이터 관리"에서 KEV를 가져왔는지 확인(시험 모드로도 볼 수 있음)
