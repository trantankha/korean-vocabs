"use client";

import { ArrowRight, Languages, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { api } from "@/lib/api";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);

    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");
        setBusy(true);
        try {
            if (mode === "login") await api.auth.login(email, password);
            else await api.auth.register(email, password);
            router.replace("/dashboard");
            router.refresh();
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Authentication failed.");
        } finally {
            setBusy(false);
        }
    }

    return (
        <main className="auth-shell">
            <aside className="auth-aside">
                <Link className="brand" href="/login" aria-label="Korean Vocab home">
                    <span className="brand-mark">가</span><span>Korean Vocab</span>
                </Link>
                <div className="auth-aside-copy">
                    <p className="eyebrow">A PERSONAL WORDBOOK</p>
                    <h1>Make every<br />new word <em>stay.</em></h1>
                    <p className="aside-note">A small, steady place for the Korean words you want to remember.</p>
                    <div className="word-stamp" aria-label="Korean word examples">
                        <span className="stamp-korean">마음</span>
                        <span className="stamp-meaning">ma-eum · heart, mind</span>
                        <span className="stamp-rule" />
                        <span className="stamp-korean small-stamp">천천히</span>
                        <span className="stamp-meaning">slowly, at your own pace</span>
                    </div>
                </div>
                <div className="auth-aside-foot"><span>01</span><span>Words collected with intention</span></div>
            </aside>

            <section className="auth-main">
                <div className="auth-mobile-brand"><span className="brand-mark">가</span>Korean Vocab</div>
                <div className="auth-form-wrap">
                    <p className="eyebrow">YOUR WORDBOOK, WAITING</p>
                    <h2>{mode === "login" ? "Welcome back" : "Start your wordbook"}</h2>
                    <p className="auth-subtitle">{mode === "login" ? "Pick up where your Korean left off." : "Create a quiet place for the words you meet."}</p>
                    <div className="auth-tabs" role="tablist" aria-label="Account action">
                        <Link className={mode === "login" ? "active" : ""} href="/login" role="tab" aria-selected={mode === "login"}>Sign in</Link>
                        <Link className={mode === "register" ? "active" : ""} href="/register" role="tab" aria-selected={mode === "register"}>Create account</Link>
                    </div>
                    <form className="auth-form" onSubmit={submit}>
                        <label htmlFor="email">Email</label>
                        <input autoComplete="email" id="email" onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required type="email" value={email} />
                        <div className="label-line">
                            <label htmlFor="password">Password</label>
                            {mode === "register" && <span>At least 8 characters</span>}
                        </div>
                        <input autoComplete={mode === "login" ? "current-password" : "new-password"} id="password" minLength={8} onChange={(event) => setPassword(event.target.value)} placeholder="8 characters or more" required type="password" value={password} />
                        {error && <p className="form-error" role="alert">{error}</p>}
                        <button className="button button-primary auth-submit" disabled={busy} type="submit">
                            {busy ? <LoaderCircle className="spin" size={17} /> : null}
                            {busy ? "One moment…" : mode === "login" ? "Open my wordbook" : "Create my wordbook"}
                            {!busy && <ArrowRight size={17} />}
                        </button>
                    </form>
                    <p className="auth-footnote"><Languages size={15} /> Made for the words you find along the way.</p>
                </div>
            </section>
        </main>
    );
}