import type { KevRepository, MatchRepository, RiskView } from "@/application/ports";
import { computeScore } from "@/domain/scoring";
import { findCandidates } from "@/domain/matching";
import type { Asset, MatchStatus } from "@/domain/types";

// [B 소유] 매칭 저장소의 가짜 구현. 자산 × KEV로 후보를 메모리에서 만든다. B가 Supabase 구현으로 바꾼다.
export function createFakeMatchRepository(getAssets: () => Promise<Asset[]>, kev: KevRepository): MatchRepository {
  const decided = new Map<string, { status: MatchStatus; note: string }>();
  const today = () => new Date().toISOString().slice(0, 10);

  async function all(): Promise<RiskView[]> {
    const [assets, entries] = await Promise.all([getAssets(), kev.list()]);
    return assets.flatMap((asset) =>
      findCandidates(asset, entries).map((entry): RiskView => {
        const matchId = `${asset.id}|${entry.cveId}`;
        const score = computeScore(asset, entry, today());
        const choice = decided.get(matchId);
        return {
          matchId, asset, entry, status: choice?.status ?? "candidate", note: choice?.note,
          score: score.total, scoreBreakdown: score.breakdown,
        };
      }),
    );
  }

  const filter = (rows: RiskView[], status?: MatchStatus) => (status ? rows.filter((row) => row.status === status) : rows);
  return {
    upsertCandidates: async () => (await all()).length,
    listForOwner: async (_ownerId, status) => filter(await all(), status),
    listAll: async (status) => filter(await all(), status),
    decide: async (matchId, status, note) => void decided.set(matchId, { status, note }),
  };
}
