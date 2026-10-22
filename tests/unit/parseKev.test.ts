import { describe, expect, it } from "vitest";
import { KevParseError, parseKev } from "@/infrastructure/kev/parseKev";

const raw = {
  catalogVersion: "2026.10.21",
  vulnerabilities: [
    {
      cveID: "CVE-TEST-1", vendorProject: "Fortinet", product: "FortiOS", vulnerabilityName: "n",
      dateAdded: "2026-10-01", dueDate: "2026-10-08", knownRansomwareCampaignUse: "Known",
      shortDescription: "d", requiredAction: "a", notes: "모르는 열", cwes: ["CWE-78"], forensicTriage: "Yes",
    },
    { vendorProject: "cveID 없음" },
  ],
};

describe("parseKev (R-05, S-04, S-05)", () => {
  it("KEV 항목을 우리 형식으로 바꾸고 모르는 열은 무시한다", () => {
    const result = parseKev(raw);
    expect(result.status).toBe("ok");
    expect(result.catalogVersion).toBe("2026.10.21");
    expect(result.entries).toHaveLength(1);
    expect(result.entries[0].ransomwareKnown).toBe(true);
  });

  it("항목이 없으면 '내용 없음'이다", () => {
    expect(parseKev({ catalogVersion: "x", vulnerabilities: [] }).status).toBe("empty");
  });

  it("형식이 다르면 오류를 던져 '못 읽음'으로 처리하게 한다", () => {
    expect(() => parseKev({ nope: true })).toThrow(KevParseError);
    expect(() => parseKev(null)).toThrow(KevParseError);
  });
});
