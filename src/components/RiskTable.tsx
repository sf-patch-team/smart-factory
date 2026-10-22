import type { RiskRow } from "@/application/demoRisks";

const BREAKDOWN_LABELS = [
  ["overdue", "기한 초과"],
  ["ransomware", "랜섬웨어"],
  ["criticality", "중요도"],
  ["recency", "최근 등록"],
] as const;

// R-09: 점수와 점수 구성을 항상 함께 보여 준다.
export function RiskTable({ rows }: { rows: RiskRow[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th className="num">점수</th>
            <th>자산</th>
            <th>취약점</th>
            <th>점수 구성</th>
            <th className="num">기한 초과(일)</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr><td className="empty" colSpan={5}>해당하는 위험이 없어요</td></tr>
          )}
          {rows.map(({ asset, entry, score }) => (
            <tr key={`${asset.id}-${entry.cveId}`}>
              <td className="num"><strong>{score.total}</strong></td>
              <td>{asset.name}<br /><span className="screen-id">{asset.vendor} {asset.product}</span></td>
              <td>{entry.cveId}<br /><span className="screen-id">{entry.vulnerabilityName}</span></td>
              <td className="screen-id">
                {BREAKDOWN_LABELS.map(([key, label]) => `${label} ${score.breakdown[key]}`).join(" · ")}
              </td>
              <td className="num">{score.overdueDays}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
