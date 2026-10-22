import Link from "next/link";

// AU-01-P 뼈대: Supabase 연결 전이라 버튼은 아직 동작하지 않는다(R-01은 다음 단계).
export default function LoginPage() {
  return (
    <main className="content" style={{ margin: "0 auto", maxWidth: 420 }}>
      <div className="page-head">
        <h1>로그인</h1>
        <span className="screen-id">AU-01-P</span>
      </div>
      <form className="card">
        <div className="field">
          <label htmlFor="email">이메일</label>
          <input id="email" type="email" autoComplete="email" />
        </div>
        <div className="field">
          <label htmlFor="password">비밀번호</label>
          <input id="password" type="password" autoComplete="current-password" />
        </div>
        <button className="btn primary" type="button" disabled>로그인하기</button>
      </form>
      <p className="notice" style={{ marginTop: 16 }}>
        로그인 연결은 Supabase 설정 뒤에 켜져요. <Link href="/signup">회원가입</Link>
      </p>
    </main>
  );
}
