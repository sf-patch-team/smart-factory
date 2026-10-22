import { PagePlaceholder } from "@/components/PagePlaceholder";

// AD-07-P (A 소유): 관리자용 요청 상세·승인·반려. 담당자용 RQ-03-P(C 소유)와 화면을 나눠 서로 겹치지 않게 한다.
export default async function AdminRequestDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <PagePlaceholder
      screenId="AD-07-P"
      title={`요청 상세·승인 ${id}`}
      lead="근거(점수 구성·호환성 확인 결과)를 보고 승인하거나 반려해요. (연결 예정)"
      columns={["시각", "행위자", "이전 상태", "새 상태", "사유"]}
    />
  );
}
