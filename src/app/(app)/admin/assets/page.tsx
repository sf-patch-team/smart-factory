import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function AdminAssetsPage() {
  return (
    <PagePlaceholder
      screenId="AD-03-P"
      title="전체 자산"
      lead="모든 담당자의 자산을 봐요. (연결 예정)"
      columns={["이름", "담당자", "벤더·제품", "구분", "중요도"]}
    />
  );
}
