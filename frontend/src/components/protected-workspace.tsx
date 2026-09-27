"use client";

import { BookOpen, LayoutDashboard, LoaderCircle, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { ApiError, api, type User } from "@/lib/api";

export function ProtectedWorkspace({ children }: { children: ReactNode }) {
    const pathname = usePathname();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;
        api.auth.me()
            .then((currentUser) => { if (active) setUser(currentUser); })
            .catch((reason: unknown) => {
                if (!active) return;
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
                else setError(reason instanceof Error ? reason.message : "Unable to verify your session.");
            });
        return () => { active = false; };
    }, [router]);

    async function logout() {
        try {
            await api.auth.logout();
        } finally {
            router.replace("/login");
            router.refresh();
        }
    }

    if (!user) {
        return (
            <main className="loading-screen">
                <span className="brand-mark" aria-hidden="true">가</span>
                {error ? <p role="alert">{error}</p> : <><LoaderCircle className="spin" size={20} /><p>Restoring your library</p></>}
            </main>
        );
    }

    const dashboardActive = pathname.startsWith("/dashboard");
    const vocabularyActive = pathname.startsWith("/vocabulary");

    return (
        <main className="workspace-shell">
            <aside className="sidebar">
                <Link className="brand sidebar-brand" href="/dashboard"><span className="brand-mark">가</span><span>Korean Vocab</span></Link>
                <div className="sidebar-label">YOUR SPACE</div>
                <nav className="side-nav" aria-label="Main navigation">
                    <Link className={`nav-item${dashboardActive ? " active" : ""}`} href="/dashboard"><LayoutDashboard size={18} /> Dashboard</Link>
                    <Link className={`nav-item${vocabularyActive ? " active" : ""}`} href="/vocabulary"><BookOpen size={18} /> Word library</Link>
                </nav>
                <div className="sidebar-bottom">
                    <div className="profile-row">
                        <span className="avatar">{user.email.slice(0, 1).toUpperCase()}</span>
                        <span className="profile-email">{user.email}</span>
                        <button className="icon-button subtle-icon" onClick={logout} title="Sign out" aria-label="Sign out"><LogOut size={16} /></button>
                    </div>
                    <p className="sidebar-version">A little progress, every day.</p>
                </div>
            </aside>
            <section className="main-panel">
                <header className="topbar">
                    <div className="breadcrumb"><span>My space</span><span aria-hidden="true">/</span><strong>{dashboardActive ? "Dashboard" : "Word library"}</strong></div>
                    <button className="mobile-signout" onClick={logout} aria-label="Sign out"><LogOut size={17} /></button>
                    <div className="topbar-note">Korean, gathered at your pace</div>
                </header>
                {children}
            </section>
        </main>
    );
}