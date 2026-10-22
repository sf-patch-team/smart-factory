import type { Asset, Category, Criticality } from "@/domain/types";

// 가상 공장의 자산(FR-21). 실제 회사·개인 정보 없음.
// 구조는 공장 계층(구역 → 라인 → 자산)으로 설계했다. 설계 기반 가상 데이터이며,
// BPI 2013·2014 통계는 아직 반영하지 않았다(4TU 접속 불가, docs/00 참고).
// KEV와 맞을 것 / 제품이 달라 안 맞을 것 / 벤더가 없어 안 맞을 것을 섞었다.
type Spec = {
  type: string;
  vendor: string;
  product: string;
  version: string;
  category: Category;
  criticality: Criticality;
  constraints: string[];
  rollback: boolean;
  count: number;
};

type Zone = { zone: string; lines: string[]; specs: Spec[] };

const spec = (
  type: string, vendor: string, product: string, version: string, category: Category,
  criticality: Criticality, constraints: string[], rollback: boolean, count = 1,
): Spec => ({ type, vendor, product, version, category, criticality, constraints, rollback, count });

const OT_LOCKED = ["no_downtime", "vendor_approval"];
const PLC_MITSUBISHI = spec("PLC", "Mitsubishi Electric", "iQ-R R04CPU", "1.0", "OT", "high", OT_LOCKED, false, 2);
const PLC_SIEMENS = spec("통신 모듈", "Siemens", "SIMATIC CP 1543", "V3.0", "OT", "high", ["vendor_approval", "maintenance_window"], false, 2);
const HMI = spec("HMI PC", "Microsoft", "Windows 10 IoT", "21H2", "OT", "high", OT_LOCKED, false, 2);
const SWITCH = spec("산업용 스위치", "Moxa", "EDS-508A", "3.9", "OT", "mid", ["maintenance_window"], true, 2);
const GATEWAY = spec("게이트웨이", "Advantech", "ADAM-6000", "2.1", "OT", "low", [], true);
const FACTORYTALK = spec("공정 소프트웨어", "Rockwell Automation", "FactoryTalk View", "13.0", "OT", "high", ["vendor_approval"], false);
const MOTION = spec("모션 컨트롤러", "Beckhoff", "CX5140", "TC3", "OT", "mid", ["vendor_approval"], false);

const ZONES: Zone[] = [
  { zone: "프레스동", lines: ["프레스 라인 1", "프레스 라인 2", "프레스 라인 3"], specs: [PLC_MITSUBISHI, HMI, SWITCH] },
  { zone: "조립동", lines: ["조립 라인 1", "조립 라인 2", "조립 라인 3", "조립 라인 4"], specs: [PLC_SIEMENS, HMI, SWITCH, GATEWAY] },
  { zone: "도장동", lines: ["도장 라인 1", "도장 라인 2"], specs: [FACTORYTALK, PLC_MITSUBISHI, HMI, MOTION] },
  { zone: "포장·물류동", lines: ["포장 라인 1", "물류 라인 1"], specs: [PLC_MITSUBISHI, HMI, GATEWAY] },
  { zone: "품질검사동", lines: ["검사 라인 1", "검사 라인 2"], specs: [MOTION, HMI, SWITCH] },
  {
    zone: "수전·유틸리티동", lines: ["수전 설비"],
    specs: [spec("전력 컨트롤러", "Schneider Electric", "Modicon M580", "3.20", "OT", "high", OT_LOCKED, false, 3), SWITCH],
  },
  {
    zone: "중앙 제어실", lines: ["제어실"],
    specs: [
      spec("SCADA 서버", "Microsoft", "Windows Server", "2019", "OT", "high", ["maintenance_window"], true, 2),
      spec("엔지니어링 PC", "Microsoft", "Windows 11", "23H2", "OT", "mid", ["maintenance_window"], true, 4),
      spec("공정 소프트웨어", "Rockwell Automation", "FactoryTalk View", "13.0", "OT", "high", ["vendor_approval"], false, 2),
    ],
  },
  {
    zone: "데이터센터", lines: ["서버실"],
    specs: [
      spec("가상화 서버", "VMware", "ESXi", "7.0", "IT", "high", ["no_downtime"], false, 3),
      spec("윈도우 서버", "Microsoft", "Windows Server", "2019", "IT", "mid", ["maintenance_window"], true, 5),
      spec("메일 서버", "Microsoft", "Exchange Server", "2019", "IT", "low", [], true),
      spec("백업 서버", "Veeam", "Backup & Replication", "12", "IT", "mid", [], true),
    ],
  },
  {
    zone: "경계망·원격접속", lines: ["외부 연결"],
    specs: [
      spec("방화벽", "Fortinet", "FortiOS", "7.2", "IT", "high", ["maintenance_window"], true, 4),
      spec("보안장비", "Cisco", "Adaptive Security Appliance (ASA)", "9.16", "IT", "high", ["vendor_approval"], false),
      spec("방화벽", "Palo Alto Networks", "PAN-OS", "10.2", "IT", "high", ["maintenance_window"], true, 2),
      spec("원격접속 VPN", "Ivanti", "Connect Secure", "22.4", "IT", "high", [], true, 2),
      spec("원격접속 SMA", "SonicWall", "SMA 100 Series", "10.2", "IT", "mid", [], true),
      spec("방화벽", "Zyxel", "USG FLEX", "5.3", "IT", "low", [], true),
      spec("라우터", "Cisco", "IOS XE", "17.6", "IT", "mid", [], true, 3),
    ],
  },
];

const pad = (n: number): string => String(n).padStart(2, "0");

function buildAssets(zone: Zone, zoneIndex: number): Asset[] {
  return zone.lines.flatMap((line, lineIndex) =>
    zone.specs.flatMap((item, specIndex) =>
      Array.from({ length: item.count }, (_, i): Asset => ({
        id: `seed-${pad(zoneIndex + 1)}-${pad(lineIndex + 1)}-${pad(specIndex + 1)}-${pad(i + 1)}`,
        name: `${line} ${item.type}(${item.vendor}) ${pad(i + 1)}`,
        vendor: item.vendor,
        product: item.product,
        version: item.version,
        category: item.category,
        assetType: item.type,
        zone: zone.zone,
        line,
        criticality: item.criticality,
        affectedEquipment: line,
        patchConstraints: item.constraints,
        rollbackPossible: item.rollback,
      })),
    ),
  );
}

export const SEED_ASSETS: Asset[] = ZONES.flatMap(buildAssets);
