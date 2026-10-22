import type { AssetRepository } from "@/application/ports";
import type { Asset } from "@/domain/types";
import { SEED_ASSETS } from "@/infrastructure/seed/assets";

// [C 소유] 자산 저장소의 가짜 구현(가상 자산 115개, 메모리). C가 Supabase 구현으로 바꾼다.
export function createFakeAssetRepository(initial: Asset[] = SEED_ASSETS): AssetRepository {
  const assets = new Map(initial.map((asset) => [asset.id, asset]));
  return {
    listForOwner: async () => [...assets.values()], // 가짜는 소유자를 가리지 않는다
    listAll: async () => [...assets.values()],
    save: async (asset) => {
      assets.set(asset.id, asset);
      return asset;
    },
  };
}
