import { PagePlaceholder } from "@/components/PagePlaceholder";

export default function NewRequestPage() {
  return (
    <PagePlaceholder
      screenId="RQ-02-P"
      title="새 패치 요청"
      lead="신청 전에 호환성 확인 체크리스트를 채워요. 앱이 호환 여부를 판정하지는 않아요. (연결 예정)"
      columns={["확인 항목", "답", "메모"]}
    />
  );
}
