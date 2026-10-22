import { PagePlaceholder } from "@/components/PagePlaceholder";

// 가능하면(Could) 화면: 요청 상태 이력으로 소요 시간을 계산한다(spec R-24).
export default function AdminStatsPage() {
  return (
    <PagePlaceholder
      screenId="AD-06-P"
      title="통계"
      lead="요청에서 완료까지 걸린 시간, 기한 초과율 등을 봐요. (후순위)"
      columns={["지표", "값", "기준"]}
    />
  );
}
