import Link from "next/link";

// AU-02-P 뼈대: 가입한 사용자의 기본 역할은 담당자다(R-01).
export default function SignupPage() {
  return (
    <main className="content" style={{ margin: "0 auto", maxWidth: 420 }}>
      <div className="page-head">
        <h1>회원가입</h1>
        <span className="screen-id">AU-02-P</span>
      </div>
      <form className="card">
        <div className="field">
          <label htmlFor="name">이름 (가상 이름을 써 주세요)</label>
          <input id="name" type="text" autoComplete="name" />
        </div>
        <div className="field">
          <label htmlFor="email">이메일</label>
          <input id="email" type="email" autoComplete="email" />
        </div>
        <div className="field">
          <label htmlFor="password">비밀번호</label>
          <input id="password" type="password" autoComplete="new-password" />
        </div>
        <button className="btn primary" type="button" disabled>가입하기</button>
      </form>
      <p className="notice" style={{ marginTop: 16 }}>
        가입 연결은 Supabase 설정 뒤에 켜져요. <Link href="/login">로그인</Link>
      </p>
    </main>
  );
}
