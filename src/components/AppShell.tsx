import Link from "next/link";

const MEMBER_LINKS = [
  { href: "/", label: "대시보드" },
  { href: "/risks", label: "위험 항목" },
  { href: "/assets", label: "자산" },
  { href: "/requests", label: "패치 요청" },
];

const ADMIN_LINKS = [
  { href: "/admin", label: "관리 대시보드" },
  { href: "/admin/requests", label: "승인 대기" },
  { href: "/admin/assets", label: "전체 자산" },
  { href: "/admin/history", label: "전체 이력" },
  { href: "/admin/data", label: "데이터 관리" },
];

// 뼈대 단계: 로그인 연결 전이라 관리 메뉴를 함께 보여 준다. 연결 뒤에는 역할로 나눈다(R-02).
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="shell">
      <nav className="sidebar" aria-label="주 메뉴">
        <strong>smart-factory</strong>
        <p className="nav-title">담당자</p>
        {MEMBER_LINKS.map((link) => (
          <Link key={link.href} href={link.href}>{link.label}</Link>
        ))}
        <p className="nav-title">관리자</p>
        {ADMIN_LINKS.map((link) => (
          <Link key={link.href} href={link.href}>{link.label}</Link>
        ))}
      </nav>
      <main className="content">{children}</main>
      <nav className="tabbar" aria-label="하단 메뉴">
        {MEMBER_LINKS.map((link) => (
          <Link key={link.href} href={link.href}>{link.label}</Link>
        ))}
        <Link href="/admin">관리</Link>
      </nav>
    </div>
  );
}
