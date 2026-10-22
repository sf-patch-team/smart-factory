import type { KevEntry } from "@/domain/types";

export type KevCatalog = {
  catalogVersion: string;
  entries: KevEntry[];
  status: "ok" | "empty";
};

export class KevParseError extends Error {}

type RawEntry = Record<string, unknown>;

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function toEntry(raw: RawEntry): KevEntry | null {
  const cveId = text(raw.cveID);
  if (!cveId) return null;
  return {
    cveId,
    vendorProject: text(raw.vendorProject),
    product: text(raw.product),
    vulnerabilityName: text(raw.vulnerabilityName),
    dateAdded: text(raw.dateAdded),
    dueDate: text(raw.dueDate),
    ransomwareKnown: raw.knownRansomwareCampaignUse === "Known",
    shortDescription: text(raw.shortDescription),
    requiredAction: text(raw.requiredAction),
  };
}

// 모르는 열은 무시한다. 형식이 달라지면 "못 읽음"으로 처리하도록 오류를 던진다.
export function parseKev(json: unknown): KevCatalog {
  const body = json as { catalogVersion?: unknown; vulnerabilities?: unknown } | null;
  if (!body || !Array.isArray(body.vulnerabilities)) {
    throw new KevParseError("KEV 형식이 달라서 읽지 못했어요.");
  }
  const entries = body.vulnerabilities
    .map((raw) => toEntry(raw as RawEntry))
    .filter((entry): entry is KevEntry => entry !== null);
  return {
    catalogVersion: text(body.catalogVersion),
    entries,
    status: entries.length === 0 ? "empty" : "ok",
  };
}
