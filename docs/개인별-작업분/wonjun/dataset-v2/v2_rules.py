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

# 제조사 고유 통신(예시). 포트는 널리 알려진 값이나 장비 설정에 따라 다르다. 실제 지원 여부는 미검증.
VENDOR_FLOW_SHARE = 0.5
VENDOR_FLOWS = {
    "Siemens": {"port": 102, "purpose": "가상 PLC/CNC 데이터 읽기(ISO-on-TCP 계열 예시)", "note": "포트 102는 Siemens 계열 통신에 흔히 쓰이는 예시. 실제 장비 지원·설정 미검증"},
    "LS ELECTRIC": {"port": 2004, "purpose": "가상 PLC 데이터 읽기(LS XGT 전용 통신 계열 예시)", "note": "2004는 흔히 쓰이는 예시 포트. 실제 설정·지원 미검증"},
    "Mitsubishi Electric": {"port": 5007, "purpose": "가상 PLC 데이터 읽기(SLMP 계열 예시)", "note": "5007은 설정 가능한 예시 포트. 실제 장비 설정 미검증"},
}

# 비판에서 빠졌다고 지적된 설비 자산(사이트마다 추가). 제조사·제품은 가상 이름이며 펌웨어·버전은 모델링하지 않는다.
EXTRA_ASSETS = [
    # (assetType, 개수, category, segment 접미, owner 접미, 제품명, criticality, 제약, exposure, rollback)
    ("3차원 측정기 PC", 1, "OT", "SCADA", "OT", "SIM-CMM-PC", "mid", ["maintenance_window"], "internal", True),
    ("공구 프리셋 PC", 1, "OT", "SCADA", "OT", "SIM-TOOL-PRESET", "low", [], "internal", True),
    ("절삭유·칩 처리 PLC", 1, "OT", "SCADA", "OT", "SIM-COOLANT-PLC", "mid", ["no_downtime"], "internal", False),
    ("컴프레서 제어 PLC", 1, "OT", "SCADA", "OT", "SIM-COMPRESSOR-PLC", "mid", ["no_downtime"], "internal", False),
    ("원격 유지보수 게이트웨이", 1, "OT", "DMZ", "OT", "SIM-REMOTE-GW", "high", ["vendor_approval", "maintenance_window"], "remote", True),
    ("산업용 무선 AP", 2, "IT", "OFFICE", "IT", "SIM-INDUSTRIAL-AP", "mid", ["maintenance_window"], "internal", True),
]
EXTRA_VENDOR = "가상 설비 공급사"

EPSS_DATE = "2026-10-22"          # EPSS는 시험용 값이며 이 날짜는 가정이다
AS_OF_MONTH = "2026-10"

# 설비 구성의 다양화(현실의 혼합). 새 제품에는 펌웨어·버전을 모델링하지 않는다(미상).
# (확률, (제조사, 제품, 버전)). 현재 값과 같으면 건너뛴다.
WIN10 = ("Microsoft", "Windows 10 Enterprise", "22H2")
WIN11 = ("Microsoft", "Windows 11", "23H2")
LTSC = ("Microsoft", "Windows 10 IoT Enterprise LTSC", "2021")
FLEET_MIX = {                      # 라인에 속하지 않는 공용 자산만 자산 단위로 섞는다
    "업무 PC": [(0.22, WIN10), (0.04, LTSC)],
    "엔지니어링 PC": [(0.5, WIN11)],
}
OS_TYPES = ("업무 PC", "HMI PC", "엔지니어링 PC", "비전 검사 PC")
UNKNOWN_OS_CHANCE = 0.06          # 버전을 모르는 PC
NEVER_VERIFIED_CHANCE = 0.08      # 한 번도 확인한 적 없는 자산
NO_OWNER_CHANCE = 0.05            # 담당자 미지정
NO_IP_CHANCE = 0.03               # IP 미할당(DHCP 누락 등)
UNKNOWN_FIRMWARE_CHANCE = 0.10        # 펌웨어를 모르는 제어기

# ---------------- 공정(라인) 프로필 ----------------
# 단순 공정(세척·이송)은 LS ELECTRIC, 복잡한 공정(절삭·밀링·비전)은 Mitsubishi·Siemens·FANUC를 주로 쓴다.
# 한 라인은 같은 제조사로 통일하고, 가끔 새로 추가된 설비 한두 대만 다르다.
LS = "LS ELECTRIC"
LS_PLC = [(0.5, (LS, "XGK-CPUU", None)), (0.3, (LS, "XGI-CPUU", None)), (0.2, (LS, "XBC-DN32U", None))]
MITSU_PLC = ("Mitsubishi Electric", "MELSEC iQ-R R04CPU", None)
SIEMENS_PLC = ("Siemens", "SIMATIC S7-1500", None)
LINE_PLC = [(0.70, "LS"), (0.20, MITSU_PLC), (0.10, SIEMENS_PLC)]           # 세척·이송 셀의 PLC
LINE_CNC = [(0.45, ("Siemens", "SINUMERIK 840D sl", None)), (0.35, ("FANUC", "Series 0i-MF Plus", None)),
            (0.20, ("Mitsubishi Electric", "M80", None))]
LINE_ROBOT = [(0.75, ("FANUC", "R-30iB Plus", None)), (0.25, ("Yaskawa", "YRC1000", None))]
LINE_INVERTER = [(0.65, (LS, "LSLV-H100", None)), (0.35, ("Mitsubishi Electric", "FR-A800", None))]
LINE_SWITCH = [(0.70, ("Moxa", "EDS-516A", None)), (0.20, ("Siemens", "SCALANCE XC208", None)), (0.10, ("Cisco", "IE-3300", None))]
LINE_ADDITION_CHANCE = 0.10        # 라인마다 새로 추가된 설비가 다른 제조사일 확률
# 도입 시기(웨이브)별 OS와 도입 연도. 앞쪽 라인이 오래된 라인이다.
WAVES = [(0.4, "old", [2019, 2020, 2021], {"hmi": LTSC, "vision": WIN10}),
         (0.8, "mid", [2022, 2023], {"hmi": LTSC, "vision": LTSC}),
         (1.0, "new", [2024, 2025], {"hmi": WIN11, "vision": WIN11})]
TYPE_KEY = {"CNC 컨트롤러": "cnc", "로봇 컨트롤러": "robot", "PLC": "plc", "인버터": "inverter", "산업용 스위치": "switch",
            "HMI PC": "hmi", "비전 검사 PC": "vision"}

# ---------------- 서버 계층 ----------------
# 서버 자산에 OS와 응용 프로그램을 설치 목록(software_installations)으로 따로 적는다.
WS2016 = ("Microsoft", "Windows Server", "2016")
WS2019 = ("Microsoft", "Windows Server", "2019")
WS2022 = ("Microsoft", "Windows Server", "2022")
RHEL8 = ("Red Hat", "Red Hat Enterprise Linux", "8")
KEP = ("PTC Kepware", "KEPServerEX", None)
IGN80 = ("Inductive Automation", "Ignition", "8.0")
IGN81 = ("Inductive Automation", "Ignition", "8.1")
WINCC = ("Siemens", "SIMATIC WinCC", None)
SQL2017 = ("Microsoft", "SQL Server", "2017")
ORA19 = ("Oracle", "Oracle Database", "19c")
SERVER_SOFTWARE = {      # 서버 종류: (OS 후보, 응용 후보). None은 가상 공급사 응용만 둠
    "OPC 수집 서버": ([(0.55, WS2019), (0.25, WS2016), (0.20, WS2022)], [(0.60, KEP), (0.15, IGN80), (0.15, IGN81), (0.10, None)]),
    "SCADA 서버": ([(0.50, WS2019), (0.35, WS2016), (0.15, WS2022)], [(0.50, WINCC), (0.15, IGN80), (0.20, IGN81), (0.15, None)]),
    "MES 앱 서버": ([(0.50, WS2019), (0.30, WS2022), (0.20, RHEL8)], []),
    "ERP 연계 서버": ([(0.60, WS2019), (0.40, RHEL8)], []),
    "품질관리 서버": ([(0.70, WS2019), (0.30, WS2022)], []),
    "물류관리 서버": ([(0.70, WS2019), (0.30, WS2022)], []),
}
DB_SERVER = [(0.70, SQL2017[:2] + ("2019",)), (0.20, SQL2017), (0.10, ORA19)]   # MES DB 서버의 주 제품

# ---------------- 라인 유형별 구조(가정) ----------------
# 설비 수의 범위는 제가 가정한 값이다. 실제 현장 값은 사용자가 확인해야 한다.
LINE_TYPE_SHARE = [("가공", 0.5), ("세척·검사", 0.25), ("조립·포장", 0.25)]
LINE_TYPES = {
    "가공": {"ops": ["소재 투입", "절삭·밀링", "디버링"], "bottleneck": "절삭·밀링",
            "counts": {"CNC 컨트롤러": (6, 8), "로봇 컨트롤러": (2, 4), "PLC": (3, 3), "인버터": (2, 2), "비전 검사 PC": (1, 1),
                       "산업용 스위치": (2, 2), "HMI PC": (1, 2), "바코드 리더": (2, 2), "엣지 수집 PC": (1, 1), "안돈 단말": (1, 1)}},
    "세척·검사": {"ops": ["세척", "치수·비전 검사"], "bottleneck": "세척",
              "counts": {"CNC 컨트롤러": (0, 0), "로봇 컨트롤러": (0, 0), "PLC": (4, 5), "인버터": (4, 6), "비전 검사 PC": (2, 3),
                         "산업용 스위치": (2, 2), "HMI PC": (1, 2), "바코드 리더": (1, 1), "엣지 수집 PC": (1, 1), "안돈 단말": (1, 1)}},
    "조립·포장": {"ops": ["조립", "포장"], "bottleneck": "조립",
              "counts": {"CNC 컨트롤러": (0, 0), "로봇 컨트롤러": (2, 3), "PLC": (5, 7), "인버터": (1, 2), "비전 검사 PC": (1, 1),
                         "산업용 스위치": (2, 2), "HMI PC": (1, 2), "바코드 리더": (4, 4), "엣지 수집 PC": (1, 1), "안돈 단말": (1, 1)}},
}
EQUIPMENT_TYPES = ("CNC 컨트롤러", "PLC", "로봇 컨트롤러", "비전 검사 PC")      # 물리 설비로 등록하는 제어 자산
# 중요도: 병목 공정 + 이중화(병렬 설비) 여부로 정한다. (병목?, 병렬?) -> (확률, 값) 목록
CRIT_BY_PROCESS = {
    (True, False): [(1.0, "high")],
    (True, True): [(0.5, "high"), (0.5, "mid")],
    (False, False): [(0.2, "high"), (0.6, "mid"), (0.2, "low")],
    (False, True): [(0.6, "mid"), (0.4, "low")],
}
CRIT_BY_TYPE = {"안돈 단말": [(0.7, "low"), (0.3, "mid")], "바코드 리더": [(0.6, "low"), (0.4, "mid")], "HMI PC": [(0.5, "mid"), (0.5, "low")],
                "엣지 수집 PC": [(0.7, "mid"), (0.3, "high")], "산업용 스위치": [(0.7, "mid"), (0.3, "high")]}
# 작업 제약: 협력사 관리(제조사 번들·보증) 확률, 정비 시간 제약 확률, 무정지(단일 지점) 확률
VENDOR_APPROVAL_CHANCE = {"CNC 컨트롤러": 0.65, "로봇 컨트롤러": 0.55, "비전 검사 PC": 0.15, "인버터": 0.10, "산업용 스위치": 0.10}
PLC_VENDOR_APPROVAL = {"LS ELECTRIC": 0.10}          # 그 외 제조사 PLC는 0.40
MAINT_WINDOW_CHANCE = 0.75
NO_DOWNTIME_SINGLE_BOTTLENECK = 0.35
NO_DOWNTIME_SINGLE_OTHER = 0.15
PLC_PORT = {"LS ELECTRIC": 2004, "Mitsubishi Electric": 5007, "Siemens": 102, "Rockwell Automation": 44818}

# 패치 정책(가정): OT는 도입 시점 빌드를 대부분 유지하고 일부만 점검 때 갱신, 사무 PC는 월 패치로 최근 빌드 중심
OT_UPDATED_CHANCE = 0.25
IT_RECENT_FROM = "2026-04-01"
IT_RECENT_CHANCE = 0.8

# ---------------- 성장 과정(세대) ----------------
# 라인은 처음부터 다 만들지 않고 2~3개로 시작해 해마다 늘린다. 개설 연도와 세대 값은 모두 가정이다.
FOUNDING_YEAR = {"VMA-P1": 2018, "VMB-P1": 2019, "VMC-P1": 2018, "VMC-P2": 2022}     # 사이트 최초 라인 개설 연도
FOUNDING_DEFAULT = 2019
LAST_LINE_YEAR = 2025
LINE_CNC_ERA = {                    # 도입이 이른 라인은 Siemens 840D sl 비중이 높다(2024년 이후 개설 라인에는 넣지 않음)
    "old": [(0.50, ("Siemens", "SINUMERIK 840D sl", None)), (0.35, ("FANUC", "Series 0i-MF Plus", None)), (0.15, ("Mitsubishi Electric", "M80", None))],
    "new": [(0.30, ("Siemens", "SINUMERIK 840D sl", None)), (0.40, ("FANUC", "Series 0i-MF Plus", None)), (0.30, ("Mitsubishi Electric", "M80", None))],
}
LINE_SWITCH_ERA = {
    "old": [(0.85, ("Moxa", "EDS-516A", None)), (0.10, ("Siemens", "SCALANCE XC208", None)), (0.05, ("Cisco", "IE-3300", None))],
    "new": [(0.50, ("Moxa", "EDS-516A", None)), (0.25, ("Siemens", "SCALANCE XC208", None)), (0.25, ("Cisco", "IE-3300", None))],
}
OT_UPDATED_BY_WAVE = {"old": 0.35, "mid": 0.20, "new": 0.10}      # 오래된 라인일수록 점검 때 갱신한 설비가 많다
GEN_QUALITY = {"old": 1.8, "mid": 1.0, "new": 0.4}                # 오래된 라인일수록 대장이 부실(확인 안 함·담당 미지정)
