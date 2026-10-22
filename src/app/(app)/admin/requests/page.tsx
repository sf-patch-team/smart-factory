import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function AdminRequestsPage() {
  return (
    <PagePlaceholder
      screenId="AD-02-P"
      title="승인 대기"
      lead="신청된 요청의 근거를 보고 승인하거나 반려해요. (연결 예정)"
      columns={["요청", "자산", "점수", "신청자", "신청일"]}
    />
  );
}
