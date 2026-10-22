import { buildRiskRows } from "@/application/demoRisks";
import { DataStatusBar } from "@/components/DataStatusBar";
import { RiskTable } from "@/components/RiskTable";
import { SEED_ASSETS } from "@/infrastructure/seed/assets";
import { TEST_KEV_ENTRIES } from "@/infrastructure/seed/testKev";

export const dynamic = "force-dynamic";

// RK-01-P 뼈대: 확인·탭은 DB 연결 뒤에 붙인다.
export default function RisksPage() {
  const today = new Date().toISOString().slice(0, 10);
  const rows = buildRiskRows(SEED_ASSETS, TEST_KEV_ENTRIES, today);
  return (
    <>
      <div className="page-head">
        <h1>위험 항목</h1>
        <span className="screen-id">RK-01-P</span>
      </div>
      <DataStatusBar state="read" receivedAt="시험 데이터" testMode />
      <p className="lead">자산과 취약점이 비슷한 짝이에요. 맞는지는 담당자가 확인해요. ({rows.length}건, 시험용)</p>
      <RiskTable rows={rows} />
    </>
  );
}
