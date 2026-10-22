import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function RequestsPage() {
  return (
    <PagePlaceholder
      screenId="RQ-01-P"
      title="패치 요청"
      lead="내 요청의 진행 상태를 봐요. (연결 예정)"
      columns={["요청", "자산", "상태", "신청일", "다음에 할 사람"]}
    />
  );
}
