"""가상 공장 데이터셋 v2 — 변형 규칙 표(설계 가정). 값은 모두 시험용 가정이며 실제 회사 자료가 아니다."""

SEED = 20261024
IT_TYPES = {"MES 앱 서버", "MES DB 서버", "OPC 수집 서버", "SCADA 서버", "공정 이력 서버", "ERP 연계 서버", "품질관리 서버",
            "물류관리 서버", "연계 API 서버", "원격 작업 중계 서버", "백업 서버", "인증 서버", "로그 서버", "가상화 호스트",
            "업무 PC", "엔지니어링 PC", "코어 스위치", "방화벽"}

# (확률, 값) 목록. 합이 1이 되도록 두었다.
CRITICALITY = {
    "바코드 리더": [(0.7, "mid"), (0.3, "low")], "안돈 단말": [(1.0, "mid")], "업무 PC": [(0.65, "mid"), (0.35, "low")],
    "인버터": [(0.7, "high"), (0.3, "mid")], "엣지 수집 PC": [(0.7, "high"), (0.3, "mid")], "로그 서버": [(0.5, "mid"), (0.5, "low")],
}
LIFECYCLE = {"업무 PC": [(0.93, "active"), (0.04, "spare"), (0.03, "retired")], "바코드 리더": [(0.94, "active"), (0.06, "spare")],
             "안돈 단말": [(0.95, "active"), (0.05, "spare")], "비전 검사 PC": [(0.96, "active"), (0.04, "retired")]}
ROLLBACK_TRUE_CHANCE = {"PLC": 0.25, "인버터": 0.15}          # 프로그램·파라미터 백업이 있는 경우
ROLLBACK_FALSE_CHANCE = {"MES DB 서버": 0.2, "가상화 호스트": 0.25}   # 스냅샷·클러스터 문제로 되돌리기 어려운 경우
EXTRA_CONSTRAINT = {                                          # (자산 종류, 추가할 제약, 확률)
    ("MES DB 서버", "vendor_approval", 0.8), ("SCADA 서버", "vendor_approval", 0.6), ("OPC 수집 서버", "vendor_approval", 0.4),
    ("ERP 연계 서버", "vendor_approval", 0.4), ("MES DB 서버", "no_downtime", 0.4), ("인증 서버", "no_downtime", 0.3),
    ("HMI PC", "no_downtime", 0.3), ("비전 검사 PC", "no_downtime", 0.2),
}
CLEAR_CONSTRAINT_CHANCE = {"업무 PC": 0.7}                    # 자동 업데이트가 가능한 PC는 제약 없음

EXPOSURE = {"원격 작업 중계 서버": "remote", "연계 API 서버": "dmz", "ERP 연계 서버": "dmz", "방화벽": "perimeter"}
REMOTE_ENGINEERING_CHANCE = 0.5                                 # 엔지니어링 PC 중 원격접속 가능한 비율
EDR_CHANCE = {"업무 PC": 0.9, "엔지니어링 PC": 0.8, "HMI PC": 0.35, "비전 검사 PC": 0.5, "안돈 단말": 0.3,
              "공정 이력 서버": 0.85, "인증 서버": 0.9, "원격 작업 중계 서버": 0.9, "엣지 수집 PC": 0.4, "로그 서버": 0.4}
REBOOT_IT = ["일 02:00-05:00", "토 22:00-24:00", "일 01:00-04:00"]
REBOOT_OT = ["월 06:00-08:00", "수 06:00-08:00", "금 06:00-08:00", "일 06:00-10:00"]

# 이질성(회사별 고유 약점). 새 값은 시험용 설정이며 실제 설치 사실이 아니다.
HETERO = {
    "VMA": {"assetType": "HMI PC", "count": 6, "vendor": "Microsoft", "product": "Windows Embedded Standard 7", "version": "SP1", "key": "ws7"},
    "VMB": {"assetType": "가상화 호스트", "count": 2, "vendor": "VMware", "product": "ESXi", "version": "6.7", "key": "esxi67"},
    "VMC": {"assetType": "방화벽", "count": 4, "vendor": "Palo Alto Networks", "product": "PAN-OS", "version": "10.2", "key": "panos102"},
}

PARTS = {"SIM-PART-001": 240, "SIM-PART-002": 360, "SIM-PART-003": 180, "SIM-PART-004": 480,
         "SIM-PART-005": 300, "SIM-PART-006": 120, "SIM-PART-007": 420}
WO_PER_LINE = 14
WO_HOURS = 12
OBS_START = "2026-10-02T08:00:00+09:00"
AS_OF_HOURS = 90          # 관측·진행 기준 시각 = 시작 후 90시간

# 오염 변형(유형마다 서로 다른 표현을 여러 개)
VARIANTS = {
    "stale_ip": ["192.168.0.10", "192.168.1.50", "172.16.10.5", "10.0.0.15", "10.1.1.100", "192.168.10.254"],
    "missing_serial": ["N/A", "-", "", "미확인", "?", "TBD", "없음"],
    "status_conflict": ["폐기완료(현장가동)", "폐기(사용중)", "사용중지/가동", "예비(가동확인)"],
    "missing_version": ["", "-", "미상", "확인불가", " "],
    "stale_verification": ["2021/02/03", "2022.5.17", "21-11-09", "2020년 3월", "2023-01-15", "작년 가을"],
}
DEPARTED_FORMATS = ["{o}-LEFT-2019", "{o}-퇴사", "(구){o}", "{o}-LEFT-2022", "{o}(이동)"]
CROSS_FILE_RATE = 0.08
FILE_FOR = {"IT": "IT자산_수정본.xlsx", "OT": "설비대장_최종.xlsx"}
CROSS_LEAK = 0.1
