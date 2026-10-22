import type { Asset, Category, Criticality } from "@/domain/types";

// 가상 자산 40개(FR-21). 실제 회사·개인 정보 없음.
// KEV와 맞을 것 / 제품이 달라 안 맞을 것 / 벤더가 없어 안 맞을 것을 섞었다.
type Group = {
  label: string;
  vendor: string;
  product: string;
  version: string;
  category: Category;
  criticality: Criticality;
  equipment: string;
  constraints: string[];
  rollback: boolean;
  count: number;
};

const GROUPS: Group[] = [
  { label: "방화벽", vendor: "Fortinet", product: "FortiOS", version: "7.2", category: "IT", criticality: "high", equipment: "공장 외부망", constraints: ["maintenance_window"], rollback: true, count: 4 },
  { label: "라우터", vendor: "Cisco", product: "IOS XE", version: "17.6", category: "IT", criticality: "mid", equipment: "사무동 네트워크", constraints: [], rollback: true, count: 3 },
  { label: "보안장비", vendor: "Cisco", product: "Adaptive Security Appliance (ASA)", version: "9.16", category: "IT", criticality: "high", equipment: "공장 외부망", constraints: ["vendor_approval"], rollback: false, count: 1 },
  { label: "방화벽 PA", vendor: "Palo Alto Networks", product: "PAN-OS", version: "10.2", category: "IT", criticality: "high", equipment: "생산망 경계", constraints: ["maintenance_window"], rollback: true, count: 2 },
  { label: "원격접속 VPN", vendor: "Ivanti", product: "Connect Secure", version: "22.4", category: "IT", criticality: "high", equipment: "협력사 원격접속", constraints: [], rollback: true, count: 2 },
  { label: "원격접속 SMA", vendor: "SonicWall", product: "SMA 100 Series", version: "10.2", category: "IT", criticality: "mid", equipment: "사무동 원격접속", constraints: [], rollback: true, count: 1 },
  { label: "가상화 서버", vendor: "VMware", product: "ESXi", version: "7.0", category: "IT", criticality: "high", equipment: "데이터센터", constraints: ["no_downtime"], rollback: false, count: 2 },
  { label: "윈도우 서버", vendor: "Microsoft", product: "Windows Server", version: "2019", category: "IT", criticality: "mid", equipment: "파일·인증 서버", constraints: ["maintenance_window"], rollback: true, count: 4 },
  { label: "메일 서버", vendor: "Microsoft", product: "Exchange Server", version: "2019", category: "IT", criticality: "low", equipment: "사무동", constraints: [], rollback: true, count: 1 },
  { label: "운전 HMI PC", vendor: "Microsoft", product: "Windows 10 IoT", version: "21H2", category: "OT", criticality: "high", equipment: "조립 라인 1~4", constraints: ["no_downtime", "vendor_approval"], rollback: false, count: 4 },
  { label: "엔지니어링 PC", vendor: "Microsoft", product: "Windows 11", version: "23H2", category: "OT", criticality: "mid", equipment: "제어실", constraints: ["maintenance_window"], rollback: true, count: 2 },
  { label: "통신 모듈", vendor: "Siemens", product: "SIMATIC CP 1543", version: "V3.0", category: "OT", criticality: "high", equipment: "포장 라인", constraints: ["vendor_approval", "maintenance_window"], rollback: false, count: 2 },
  { label: "공정 소프트웨어", vendor: "Rockwell Automation", product: "FactoryTalk View", version: "13.0", category: "OT", criticality: "high", equipment: "도장 라인", constraints: ["vendor_approval"], rollback: false, count: 2 },
  { label: "전력 컨트롤러", vendor: "Schneider Electric", product: "Modicon M580", version: "3.20", category: "OT", criticality: "high", equipment: "수전실", constraints: ["no_downtime", "vendor_approval"], rollback: false, count: 2 },
  { label: "산업용 스위치", vendor: "Moxa", product: "EDS-508A", version: "3.9", category: "OT", criticality: "mid", equipment: "조립 라인", constraints: ["maintenance_window"], rollback: true, count: 3 },
  { label: "게이트웨이", vendor: "Advantech", product: "ADAM-6000", version: "2.1", category: "OT", criticality: "low", equipment: "물류 라인", constraints: [], rollback: true, count: 2 },
  { label: "모션 컨트롤러", vendor: "Beckhoff", product: "CX5140", version: "TC3", category: "OT", criticality: "mid", equipment: "검사 라인", constraints: ["vendor_approval"], rollback: false, count: 1 },
  { label: "PLC", vendor: "Mitsubishi Electric", product: "iQ-R R04CPU", version: "1.0", category: "OT", criticality: "high", equipment: "프레스 라인", constraints: ["no_downtime", "vendor_approval"], rollback: false, count: 2 },
];

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

export const SEED_ASSETS: Asset[] = GROUPS.flatMap((group, groupIndex) =>
  Array.from({ length: group.count }, (_, i): Asset => ({
    id: `seed-${pad(groupIndex + 1)}-${pad(i + 1)}`,
    name: `${group.label} ${pad(i + 1)}`,
    vendor: group.vendor,
    product: group.product,
    version: group.version,
    category: group.category,
    criticality: group.criticality,
    affectedEquipment: group.equipment,
    patchConstraints: group.constraints,
    rollbackPossible: group.rollback,
  })),
);
