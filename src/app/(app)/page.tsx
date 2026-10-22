import { buildRiskGroups } from "@/application/demoRisks";
import { DataStatusBar } from "@/components/DataStatusBar";
import { RiskTable } from "@/components/RiskTable";
import { SEED_ASSETS } from "@/infrastructure/seed/assets";
import { TEST_KEV_ENTRIES } from "@/infrastructure/seed/testKev";

export const dynamic = "force-dynamic";
const TOP_COUNT = 5;

// DB-01-P 뼈대: 지금은 가상 자산 × 시험용 KEV로 상위 위험 묶음을 보여 준다.
export default function DashboardPage() {
  const today = new Date().toISOString().slice(0, 10);
  const groups = buildRiskGroups(SEED_ASSETS, TEST_KEV_ENTRIES, today);
  return (
    <>
      <div className="page-head">
        <h1>대시보드</h1>
        <span className="screen-id">DB-01-P</span>
      </div>
      <DataStatusBar state="read" receivedAt="시험 데이터" testMode />
      <p className="lead">지금 가장 위험한 항목 상위 {TOP_COUNT}건이에요. 같은 제품·버전 자산은 묶었어요. (시험용 가짜 데이터)</p>
      <RiskTable rows={groups.slice(0, TOP_COUNT)} hiddenCount={Math.max(0, groups.length - TOP_COUNT)} />
    </>
  );
}
