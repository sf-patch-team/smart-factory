import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function AssetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <PagePlaceholder
      screenId="AS-03-P"
      title={`자산 상세 ${id}`}
      lead="후보·위험 항목·요청 이력과 자산 변경 이력을 보여 줘요. (연결 예정)"
      columns={["바뀐 시각", "바꾼 사람", "이전 값", "이후 값"]}
    />
  );
}
