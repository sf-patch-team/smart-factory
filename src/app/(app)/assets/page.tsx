import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function AssetsPage() {
  return (
    <PagePlaceholder
      screenId="AS-01-P"
      title="자산"
      lead="내가 맡은 설비·IT 자산을 등록하고 고쳐요. (연결 예정)"
      columns={["이름", "벤더·제품", "구분", "중요도", "마지막 확인일"]}
    />
  );
}
