"use client";

import { ArrowRight, LoaderCircle, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api, type DashboardStats } from "@/lib/api";

export default function DashboardPage() {
    const router = useRouter();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;
        api.dashboard.stats()
            .then((result) => { if (active) setStats(result); })
            .catch((reason: unknown) => {
                if (!active) return;
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
                else setError(reason instanceof Error ? reason.message : "Unable to load dashboard.");
            });
        return () => { active = false; };
    }, [router]);

    if (error) return <main className="page-content"><div className="inline-error" role="alert"><span>{error}</span><button onClick={() => router.refresh()}>Retry</button></div></main>;
    if (!stats) return <main className="page-content"><div className="table-state" role="status"><LoaderCircle className="spin" size={20} /> Loading your progress</div></main>;

    const highestCategoryCount = Math.max(...stats.by_category.map((category) => category.count), 1);

    return (
        <main className="page-content dashboard-content">
            <div className="page-heading">
                <div><p className="eyebrow">A LITTLE PROGRESS, EVERY DAY</p><h1>Your dashboard<span className="heading-period">.</span></h1><p className="page-description">A quiet look at the words you have gathered.</p></div>
                <Link className="button button-primary add-button" href="/vocabulary"><ArrowRight size={17} /> Open word library</Link>
            </div>
            <section className="dashboard-overview" aria-label="Vocabulary overview">
                <div className="overview-total"><span className="overview-label">TOTAL WORDS</span><strong>{stats.total_vocabulary}</strong><span className="overview-caption">in your personal wordbook</span><Sparkles className="overview-sparkle" size={19} aria-hidden="true" /></div>
                <div className="overview-used"><span className="overview-label">CATEGORIES IN USE</span><strong>{stats.categories_used}<small> / 6</small></strong><span className="overview-caption">with at least one saved word</span></div>
            </section>
            <section className="dashboard-section" aria-labelledby="level-heading">
                <div className="dashboard-section-heading"><div><p className="eyebrow">YOUR LEARNING LEVELS</p><h2 id="level-heading">Words by level</h2></div></div>
                <div className="level-summary-grid">
                    {stats.by_level.map((item) => <article className={`level-summary level-summary-${item.level.toLowerCase()}`} key={item.level}><span className="level-summary-dot" /><span className="level-summary-label">{item.level.charAt(0) + item.level.slice(1).toLowerCase()}</span><strong>{item.count}</strong><span className="level-summary-note">{item.count === 1 ? "word" : "words"}</span></article>)}
                </div>
            </section>
            <section className="dashboard-section category-breakdown" aria-labelledby="category-heading">
                <div className="dashboard-section-heading"><div><p className="eyebrow">HOW YOUR WORDS ARE SORTED</p><h2 id="category-heading">By category</h2></div><Link className="text-action" href="/vocabulary">View all words <ArrowRight size={14} /></Link></div>
                {stats.by_category.length ? <div className="category-stat-list">{stats.by_category.map((category, index) => <Link className="category-stat-row" href={`/vocabulary?category_id=${category.id}`} key={category.id}><span className={`category-dot dot-${index % 4}`} /><span className="category-stat-name"><strong>{category.name_en}</strong><small>{category.name_ko}</small></span><span className="category-bar"><span style={{ width: `${(category.count / highestCategoryCount) * 100}%` }} /></span><strong className="category-stat-count">{category.count}</strong></Link>)}</div> : <div className="dashboard-empty"><p>No categories have words yet.</p><Link className="text-action" href="/vocabulary/new">Add your first word <ArrowRight size={14} /></Link></div>}
            </section>
        </main>
    );
}