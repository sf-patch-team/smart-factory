import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function AdminHistoryPage() {
  return (
    <PagePlaceholder
      screenId="AD-04-P"
      title="전체 이력"
      lead="기간·사용자·요청으로 걸러 모든 입력과 기록을 봐요. (연결 예정)"
      columns={["시각", "행위자", "행동", "대상", "사유"]}
    />
  );
}
