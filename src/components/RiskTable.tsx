import type { RiskGroupRow } from "@/application/demoRisks";

const BREAKDOWN_LABELS = [
  ["overdue", "기한 초과"],
  ["ransomware", "랜섬웨어"],
  ["criticality", "중요도"],
  ["recency", "최근 등록"],
] as const;

type Props = { rows: RiskGroupRow[]; hiddenCount?: number };

// R-09: 점수와 점수 구성을 항상 함께 보여 준다. R-25: 같은 제품·버전 자산은 한 줄로 묶는다.
export function RiskTable({ rows, hiddenCount = 0 }: Props) {
  return (
    <>
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
            {rows.map(({ group, score }) => (
              <tr key={group.key}>
                <td className="num"><strong>{score.total}</strong></td>
                <td>
                  {group.topAsset.name}
                  {group.assets.length > 1 && <> 외 {group.assets.length - 1}대</>}
                  <br />
                  <span className="screen-id">
                    {group.topAsset.vendor} {group.topAsset.product} {group.topAsset.version}
                  </span>
                </td>
                <td>{group.entry.cveId}<br /><span className="screen-id">{group.entry.vulnerabilityName}</span></td>
                <td className="screen-id">
                  {BREAKDOWN_LABELS.map(([key, label]) => `${label} ${score.breakdown[key]}`).join(" · ")}
                </td>
                <td className="num">{score.overdueDays}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hiddenCount > 0 && <p className="notice" style={{ marginTop: 12 }}>나머지 {hiddenCount}건은 접어 두었어요.</p>}
    </>
  );
}
