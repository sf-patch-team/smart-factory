import { createBrowserClient } from "@supabase/ssr";

// 브라우저에는 공개 키(anon)만 쓴다. 서비스 키는 절대 여기에 두지 않는다.
export function createBrowserSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    throw new Error("Supabase 설정이 없어요. .env.local을 확인해 주세요.");
  }
  return createBrowserClient(url, anonKey);
}
