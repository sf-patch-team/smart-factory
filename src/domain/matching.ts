import type { Asset, KevEntry } from "./types";

const COMPANY_WORDS = new Set(["inc", "corp", "corporation", "ltd", "llc", "co", "company", "gmbh"]);
const GENERIC_PRODUCTS = new Set(["multipleproducts", "multiple", "allproducts"]);
const MIN_TOKEN_LENGTH = 3;

function tokens(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((word) => word.length > 0 && !COMPANY_WORDS.has(word));
}

function squash(text: string): string {
  return tokens(text).join("");
}

function overlaps(a: string, b: string): boolean {
  const left = squash(a);
  const right = squash(b);
  if (left.length < MIN_TOKEN_LENGTH || right.length < MIN_TOKEN_LENGTH) return false;
  return left.includes(right) || right.includes(left);
}

// 후보만 판단한다. 맞는지는 담당자가 확인한다(ADR 0001).
export function isCandidate(asset: Asset, entry: KevEntry): boolean {
  if (!overlaps(asset.vendor, entry.vendorProject)) return false;
  return GENERIC_PRODUCTS.has(squash(entry.product)) || overlaps(asset.product, entry.product);
}

export function findCandidates(asset: Asset, entries: KevEntry[]): KevEntry[] {
  return entries.filter((entry) => isCandidate(asset, entry));
}
