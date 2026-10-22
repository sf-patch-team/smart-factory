type Props = {
  screenId: string;
  title: string;
  lead: string;
  columns: string[];
  children?: React.ReactNode;
};

// 빈 화면도 표의 틀은 그대로 보인다(design-rules 3). 실제 데이터 연결 전 뼈대용.
export function PagePlaceholder({ screenId, title, lead, columns, children }: Props) {
  return (
    <>
      <div className="page-head">
        <h1>{title}</h1>
        <span className="screen-id">{screenId}</span>
      </div>
      <p className="lead">{lead}</p>
      {children}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
          </thead>
          <tbody>
            <tr><td className="empty" colSpan={columns.length}>아직 없어요</td></tr>
          </tbody>
        </table>
      </div>
    </>
  );
}
