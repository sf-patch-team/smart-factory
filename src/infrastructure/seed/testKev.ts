import type { KevEntry } from "@/domain/types";

// 시험 모드용 가짜 KEV(FR-20). ID는 TEST-로 시작해 실제 CVE와 섞이지 않는다.
function entry(
  n: number,
  vendorProject: string,
  product: string,
  fields: Partial<KevEntry> = {},
): KevEntry {
  return {
    cveId: `TEST-${String(n).padStart(4, "0")}`,
    vendorProject,
    product,
    vulnerabilityName: `${vendorProject} ${product} 시험용 취약점`,
    dateAdded: "2026-10-01",
    dueDate: "2026-10-08",
    ransomwareKnown: false,
    shortDescription: "시험용 가짜 데이터입니다.",
    requiredAction: "벤더 안내에 따라 조치하세요. (시험용)",
    ...fields,
  };
}

export const TEST_KEV_ENTRIES: KevEntry[] = [
  entry(1, "Fortinet", "FortiOS", { ransomwareKnown: true, dueDate: "2026-09-01", dateAdded: "2026-08-25" }),
  entry(2, "Cisco", "IOS XE", { dueDate: "2026-10-30", dateAdded: "2026-10-16" }),
  entry(3, "Cisco", "Adaptive Security Appliance (ASA)", { dueDate: "2026-07-01", dateAdded: "2026-06-20" }),
  entry(4, "Palo Alto Networks", "PAN-OS", { ransomwareKnown: true }),
  entry(5, "Ivanti", "Connect Secure", { ransomwareKnown: true, dueDate: "2026-08-15", dateAdded: "2026-08-01" }),
  entry(6, "SonicWall", "SMA 100 Series"),
  entry(7, "Microsoft", "Windows", { dueDate: "2026-06-10", dateAdded: "2026-05-27" }),
  entry(8, "Microsoft", "Exchange Server", { ransomwareKnown: true }),
  entry(9, "VMware", "ESXi", { dueDate: "2026-09-20", dateAdded: "2026-09-06" }),
  entry(10, "Siemens", "SIMATIC CP", { dueDate: "2026-10-26", dateAdded: "2026-10-19" }),
  entry(11, "Rockwell", "Multiple Products", { dueDate: "2026-05-01", dateAdded: "2026-04-10" }),
  entry(12, "Schneider Electric", "U.motion Builder"),
];
