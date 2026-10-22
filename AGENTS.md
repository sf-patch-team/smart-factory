# Codex 작업 진입점

기존 프로젝트다. README.md, CLAUDE.md, docs/인수인계.md를 읽고 Git 상태를 먼저 확인한다.
요구사항은 docs/PRD.md, 데이터 구조는 docs/db/erd.md와 supabase/migrations/를 확인한다.
데이터셋 변경 시 해당 폴더 README의 출처·라이선스·가상 데이터 표시를 유지한다.

사용자의 문서 최소화 지시에 따라 문서는 7개만 유지한다.
삭제된 Intent·spec·plan·IA·UJ·ADR·작업로그를 자동으로 다시 만들지 않는다.
현재 규칙·결정은 CLAUDE.md와 PRD에, 작업 기록은 docs/인수인계.md에 모은다.
기존 미커밋 변경은 보존하고 같은 파일을 다른 도구와 동시에 고치지 않는다.
한국어로 소통하고 실제 실행한 검증만 통과로 기록한다.
커밋·push·삭제·공개 범위 변경은 사용자의 요청 및 확인 규칙을 따른다.
