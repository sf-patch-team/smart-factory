import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "smart-factory — 자산 취약점 패치 관리",
  description: "우리 자산 중 지금 위험한 취약점을 찾아 패치를 요청하고 기록합니다.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
