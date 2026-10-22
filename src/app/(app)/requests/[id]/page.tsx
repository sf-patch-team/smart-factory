import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function RequestDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <PagePlaceholder
      screenId="RQ-03-P"
      title={`요청 상세 ${id}`}
      lead="현재 상태, 호환성 확인 결과, 상태 이력을 보여 줘요. (연결 예정)"
      columns={["시각", "행위자", "이전 상태", "새 상태", "사유"]}
    />
  );
}
