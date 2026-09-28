"use client";

import { ArrowLeft, ArrowRight, BookOpen, Check, GraduationCap, LoaderCircle, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api, type Category, type StudyCard, type StudyProgressSummary, type StudyResult, type VocabularyLevel } from "@/lib/api";

type StudySessionSummary = {
    studied: number;
    answered: number;
    remembered: number;
};

const SUMMARY_STORAGE_KEY = "korean-vocab-study-summary";
const levelLabels: Record<VocabularyLevel, string> = {
    BEGINNER: "Beginner",
    INTERMEDIATE: "Intermediate",
    ADVANCED: "Advanced",
};

export function StudyWorkspace() {
    const router = useRouter();
    const [categories, setCategories] = useState<Category[]>([]);
    const [totalVocabulary, setTotalVocabulary] = useState<number | null>(null);
    const [categoryId, setCategoryId] = useState("");
    const [level, setLevel] = useState("");
    const [cardLimit, setCardLimit] = useState<5 | 10 | 20>(10);
    const [cards, setCards] = useState<StudyCard[]>([]);
    const [answers, setAnswers] = useState<Record<number, StudyResult>>({});
    const [persistedIds, setPersistedIds] = useState<Set<number>>(new Set());
    const [cardIndex, setCardIndex] = useState(0);
    const [revealed, setRevealed] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [studying, setStudying] = useState(false);
    const [error, setError] = useState("");
    const [hasStarted, setHasStarted] = useState(false);

    useEffect(() => {
        let active = true;
        Promise.all([api.categories(), api.dashboard.stats()])
            .then(([categoryResult, dashboard]) => {
                if (!active) return;
                setCategories(categoryResult);
                setTotalVocabulary(dashboard.total_vocabulary);
                setError("");
            })
            .catch((reason: unknown) => {
                if (!active) return;
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
                else setError("Unable to load study options. Please try again.");
            })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, [router]);

    async function startSession() {
        setLoading(true);
        setError("");
        const params = new URLSearchParams({ limit: String(cardLimit) });
        if (categoryId) params.set("category_id", categoryId);
        if (level) params.set("level", level);

        try {
            const result = await api.study.cards(params);
            if (!result.length) {
                setCards([]);
                setHasStarted(true);
                return;
            }
            setCards(result);
            setAnswers({});
            setPersistedIds(new Set());
            setCardIndex(0);
            setRevealed(false);
            setHasStarted(true);
            setStudying(true);
        } catch (reason) {
            if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            else setError("Unable to start a study session. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    function moveToCard(nextIndex: number) {
        setCardIndex(nextIndex);
        setRevealed(false);
    }

    function chooseResult(result: StudyResult) {
        const currentCard = cards[cardIndex];
        setAnswers((current) => ({ ...current, [currentCard.id]: result }));
    }

    async function finishSession() {
        setSaving(true);
        setError("");
        try {
            for (const card of cards) {
                const result = answers[card.id];
                if (!result || persistedIds.has(card.id)) continue;
                await api.study.record(card.id, result);
                setPersistedIds((current) => new Set(current).add(card.id));
            }

            const summary: StudySessionSummary = {
                studied: cards.length,
                answered: Object.keys(answers).length,
                remembered: Object.values(answers).filter((result) => result === "REMEMBERED").length,
            };
            window.sessionStorage.setItem(SUMMARY_STORAGE_KEY, JSON.stringify(summary));
            router.push("/study/summary");
        } catch (reason) {
            if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            else setError("Unable to save your study results. Please retry.");
        } finally {
            setSaving(false);
        }
    }

    const currentCard = cards[cardIndex];
    const answeredCount = Object.keys(answers).length;
    const progressPercent = cards.length ? ((cardIndex + 1) / cards.length) * 100 : 0;

    return (
        <main className="page-content study-content">
            <div className="page-heading">
                <div><p className="eyebrow">A MOMENT WITH YOUR WORDS</p><h1>{studying ? "Flashcards" : "Study vocabulary"}<span className="heading-period">.</span></h1><p className="page-description">A word at a time, at your own pace.</p></div>
                {studying && <button className="button button-quiet study-exit" onClick={() => { setStudying(false); setError(""); }}><ArrowLeft size={16} /> End session</button>}
            </div>

            {error && <div className="inline-error study-error" role="alert"><span>{error}</span><button onClick={() => setError("")}>Dismiss</button></div>}

            {studying && currentCard ? (
                <section className="study-session" aria-label="Flashcard session">
                    <div className="study-progress-header"><span>Card {cardIndex + 1} / {cards.length}</span><span>{answeredCount} answered</span></div>
                    {cards.length < cardLimit && <p className="study-availability-note" role="status">Only {cards.length} matching {cards.length === 1 ? "word is" : "words are"} available; your session has been adjusted from {cardLimit} cards.</p>}
                    <div className="study-progress-track" role="progressbar" aria-label="Session progress" aria-valuemin={0} aria-valuemax={cards.length} aria-valuenow={cardIndex + 1}><span style={{ width: `${progressPercent}%` }} /></div>
                    <article className={`flashcard${revealed ? " is-revealed" : ""}`}>
                        <span className="flashcard-index">{String(cardIndex + 1).padStart(2, "0")}</span>
                        <span className={`level-cell level-${currentCard.level.toLowerCase()} study-level`}><span />{levelLabels[currentCard.level]}</span>
                        <h2 lang="ko">{currentCard.word}</h2>
                        {!revealed ? (
                            <button className="button button-primary reveal-button" onClick={() => setRevealed(true)}><BookOpen size={17} /> Show answer</button>
                        ) : (
                            <div className="flashcard-answer" aria-live="polite">
                                <p className="flashcard-meaning">{currentCard.meaning}</p>
                                {currentCard.example && <p className="flashcard-example" lang="ko">{currentCard.example}</p>}
                            </div>
                        )}
                    </article>
                    {revealed && <div className="judgment-row" aria-label="Your answer">
                        <button className={`judgment-button judgment-not${answers[currentCard.id] === "NOT_REMEMBERED" ? " selected" : ""}`} aria-pressed={answers[currentCard.id] === "NOT_REMEMBERED"} onClick={() => chooseResult("NOT_REMEMBERED")}><RotateCcw size={17} /> Not remembered</button>
                        <button className={`judgment-button judgment-yes${answers[currentCard.id] === "REMEMBERED" ? " selected" : ""}`} aria-pressed={answers[currentCard.id] === "REMEMBERED"} onClick={() => chooseResult("REMEMBERED")}><Check size={17} /> Remembered</button>
                    </div>}
                    <div className="study-navigation">
                        <button className="button button-quiet" disabled={cardIndex === 0 || saving} onClick={() => moveToCard(cardIndex - 1)}><ArrowLeft size={16} /> Previous</button>
                        {cardIndex < cards.length - 1
                            ? <button className="button button-primary" disabled={saving} onClick={() => moveToCard(cardIndex + 1)}>Next card <ArrowRight size={16} /></button>
                            : <button className="button button-primary" disabled={saving} onClick={finishSession}>{saving ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />}{saving ? "Saving results" : "Finish session"}</button>}
                    </div>
                </section>
            ) : hasStarted && !cards.length ? (
                <section className="study-empty" role="status">
                    <span className="study-empty-mark"><BookOpen size={22} /></span>
                    <h2>{totalVocabulary === 0 ? "Your wordbook is ready for its first word" : "No vocabulary matches these filters"}</h2>
                    <p>{totalVocabulary === 0 ? "Add a Korean word before starting a study session." : "Try another category or level."}</p>
                    <div className="study-empty-actions">
                        {totalVocabulary === 0 ? <Link className="button button-primary" href="/vocabulary/new">Add a word <ArrowRight size={16} /></Link> : <button className="button button-quiet" onClick={() => { setCategoryId(""); setLevel(""); setHasStarted(false); }}>Clear filters</button>}
                        <button className="text-action" onClick={() => setHasStarted(false)}>Study options</button>
                    </div>
                </section>
            ) : (
                <section className="study-setup" aria-labelledby="study-options-heading">
                    <div className="study-setup-heading"><span className="study-setup-icon"><GraduationCap size={20} /></span><div><p className="eyebrow">SET UP A SESSION</p><h2 id="study-options-heading">Choose your focus</h2></div></div>
                    <div className="study-filter-grid">
                        <label className="study-filter"><span>Category</span><select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">All categories</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name_en}</option>)}</select></label>
                        <label className="study-filter"><span>Level</span><select value={level} onChange={(event) => setLevel(event.target.value)}><option value="">All levels</option><option value="BEGINNER">Beginner</option><option value="INTERMEDIATE">Intermediate</option><option value="ADVANCED">Advanced</option></select></label>
                        <fieldset className="study-count-field"><legend>Cards</legend><div className="study-count-options">{([5, 10, 20] as const).map((count) => <button key={count} type="button" className={cardLimit === count ? "selected" : ""} aria-pressed={cardLimit === count} onClick={() => setCardLimit(count)}>{count}</button>)}</div></fieldset>
                    </div>
                    <div className="study-setup-footer"><span>{totalVocabulary === null ? "Loading your wordbook" : `${totalVocabulary} ${totalVocabulary === 1 ? "word" : "words"} in your library`}</span><button className="button button-primary study-start" disabled={loading || totalVocabulary === 0} onClick={startSession}>{loading ? <LoaderCircle className="spin" size={17} /> : <GraduationCap size={17} />}{loading ? "Loading" : "Start studying"}</button></div>
                </section>
            )}
        </main>
    );
}

export function StudySummary() {
    const [summary, setSummary] = useState<StudySessionSummary | null>(null);
    const [learningProgress, setLearningProgress] = useState<StudyProgressSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        let active = true;
        Promise.resolve().then(() => {
            if (!active) return;
            try {
                const stored = window.sessionStorage.getItem(SUMMARY_STORAGE_KEY);
                if (stored) {
                    const parsed: unknown = JSON.parse(stored);
                    if (isStudySessionSummary(parsed)) setSummary(parsed);
                }
            } catch {
                if (active) setSummary(null);
            }
        });
        api.study.summary()
            .then((progress) => { if (active) setLearningProgress(progress); })
            .catch((reason: unknown) => {
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, [router]);

    if (loading) return <main className="page-content"><div className="table-state" role="status"><LoaderCircle className="spin" size={20} /> Loading your summary</div></main>;
    if (!summary) return <main className="page-content"><section className="study-empty"><h2>No recent session</h2><p>Start a study session to see its summary.</p><Link className="button button-primary" href="/study">Study vocabulary <ArrowRight size={16} /></Link></section></main>;

    const percentage = summary.answered ? Math.round((summary.remembered / summary.answered) * 100) : 0;

    return (
        <main className="page-content study-content">
            <section className="session-summary" aria-labelledby="summary-heading">
                <span className="summary-check"><Check size={22} /></span>
                <p className="eyebrow">SESSION COMPLETE</p>
                <h1 id="summary-heading">Nicely done<span className="heading-period">.</span></h1>
                <p className="summary-studied">{summary.studied} {summary.studied === 1 ? "card" : "cards"} studied</p>
                <div className="summary-result-grid">
                    <div className="summary-result summary-remembered"><span>Remembered</span><strong>{summary.remembered}</strong></div>
                    <div className="summary-result summary-unanswered"><span>Not remembered</span><strong>{summary.answered - summary.remembered}</strong></div>
                </div>
                <div className="summary-score"><strong>{percentage}%</strong><span>remembered across {summary.answered} answered {summary.answered === 1 ? "card" : "cards"}</span></div>
                {summary.answered < summary.studied && <p className="summary-unanswered-note">{summary.studied - summary.answered} {summary.studied - summary.answered === 1 ? "card was" : "cards were"} left unanswered.</p>}
                {learningProgress && <div className="summary-learning-counts" aria-label="Your learning progress"><span>{learningProgress.new} New</span><span>{learningProgress.learning} Learning</span><span>{learningProgress.mastered} Mastered</span></div>}
                <div className="summary-actions"><Link className="button button-primary" href="/study"><RotateCcw size={16} /> Study again</Link><Link className="button button-quiet" href="/dashboard">Back to dashboard</Link></div>
            </section>
        </main>
    );
}

function isStudySessionSummary(value: unknown): value is StudySessionSummary {
    if (typeof value !== "object" || value === null) return false;
    const candidate = value as Record<string, unknown>;
    return Number.isInteger(candidate.studied)
        && Number.isInteger(candidate.answered)
        && Number.isInteger(candidate.remembered)
        && (candidate.studied as number) >= 0
        && (candidate.answered as number) >= 0
        && (candidate.remembered as number) >= 0
        && (candidate.remembered as number) <= (candidate.answered as number)
        && (candidate.answered as number) <= (candidate.studied as number);
}