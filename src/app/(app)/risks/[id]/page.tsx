import { PagePlaceholder } from "@/components/PagePlaceholder";

export default async function RiskDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <PagePlaceholder
      screenId="RK-04-P"
      title={`위험 항목 상세 ${id}`}
      lead="점수 구성, 자산·영향 설비, 취약점 정보를 보여 줘요. (연결 예정)"
      columns={["점수 구성", "자산", "영향 설비", "취약점"]}
    />
  );
}
