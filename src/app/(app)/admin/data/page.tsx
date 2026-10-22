import { DataStatusBar } from "@/components/DataStatusBar";
import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function AdminDataPage() {
  return (
    <PagePlaceholder
      screenId="AD-05-P"
      title="데이터 관리"
      lead="KEV를 지금 받아오고, 시험 모드를 켜고 꺼요. (연결 예정)"
      columns={["받은 시각", "방식", "상태", "개수", "버전"]}
    >
      <DataStatusBar state="empty" />
    </PagePlaceholder>
  );
}
