import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function AdminHomePage() {
  return (
    <PagePlaceholder
      screenId="AD-01-P"
      title="관리 대시보드"
      lead="승인 대기 수, 기한 초과, 최근 이력을 한눈에 봐요. 관리자만 열 수 있어요. (연결 예정)"
      columns={["항목", "건수"]}
    />
  );
}
