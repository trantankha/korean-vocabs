"use client";

import { ArrowLeft, ArrowRight, Check, ClipboardCheck, GraduationCap, LoaderCircle, RotateCcw, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api, type Category, type QuizAnswer, type QuizQuestion, type QuizQuestionSet } from "@/lib/api";

type QuizAnswerState = {
    selectedChoiceId: string;
    result?: QuizAnswer;
};

type QuizSessionSummary = {
    studied: number;
    correct: number;
};

const SUMMARY_STORAGE_KEY = "korean-vocab-quiz-summary";

export function QuizWorkspace() {
    const router = useRouter();
    const [categories, setCategories] = useState<Category[]>([]);
    const [totalVocabulary, setTotalVocabulary] = useState<number | null>(null);
    const [categoryId, setCategoryId] = useState("");
    const [level, setLevel] = useState("");
    const [questionLimit, setQuestionLimit] = useState<5 | 10 | 20>(10);
    const [questionSet, setQuestionSet] = useState<QuizQuestionSet | null>(null);
    const [answerStates, setAnswerStates] = useState<Record<string, QuizAnswerState>>({});
    const [questionIndex, setQuestionIndex] = useState(0);
    const [setupLoading, setSetupLoading] = useState(true);
    const [starting, setStarting] = useState(false);
    const [submittingToken, setSubmittingToken] = useState("");
    const [playing, setPlaying] = useState(false);
    const [error, setError] = useState("");
    const [hasStarted, setHasStarted] = useState(false);

    useEffect(() => {
        let active = true;
        Promise.all([api.categories(), api.dashboard.stats()])
            .then(([categoryResult, dashboard]) => {
                if (!active) return;
                setCategories(categoryResult);
                setTotalVocabulary(dashboard.total_vocabulary);
            })
            .catch((reason: unknown) => {
                if (!active) return;
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
                else setError("Unable to load quiz options. Please try again.");
            })
            .finally(() => { if (active) setSetupLoading(false); });
        return () => { active = false; };
    }, [router]);

    async function startQuiz() {
        setStarting(true);
        setError("");
        const params = new URLSearchParams({ limit: String(questionLimit) });
        if (categoryId) params.set("category_id", categoryId);
        if (level) params.set("level", level);

        try {
            const result = await api.quiz.questions(params);
            setQuestionSet(result);
            setAnswerStates({});
            setQuestionIndex(0);
            setHasStarted(true);
            setPlaying(result.questions.length > 0);
        } catch (reason) {
            if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            else setError("Unable to start the quiz. Please try again.");
        } finally {
            setStarting(false);
        }
    }

    async function submitAnswer(question: QuizQuestion, choiceId: string) {
        if (answerStates[question.question_token]?.result || submittingToken) return;
        setAnswerStates((current) => ({
            ...current,
            [question.question_token]: { selectedChoiceId: choiceId },
        }));
        setSubmittingToken(question.question_token);
        setError("");
        try {
            const result = await api.quiz.answer(question.question_token, choiceId);
            setAnswerStates((current) => ({
                ...current,
                [question.question_token]: { selectedChoiceId: choiceId, result },
            }));
        } catch (reason) {
            if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            else setError("Your answer could not be checked. Retry to submit the selected choice.");
        } finally {
            setSubmittingToken("");
        }
    }

    function finishQuiz() {
        if (!questionSet) return;
        const correct = Object.values(answerStates).filter((answer) => answer.result?.correct).length;
        const summary: QuizSessionSummary = { studied: questionSet.questions.length, correct };
        window.sessionStorage.setItem(SUMMARY_STORAGE_KEY, JSON.stringify(summary));
        router.push("/quiz/summary");
    }

    const questions = questionSet?.questions ?? [];
    const currentQuestion = questions[questionIndex];
    const currentAnswer = currentQuestion ? answerStates[currentQuestion.question_token] : undefined;
    const answeredCount = Object.values(answerStates).filter((answer) => answer.result).length;
    const progressPercent = questions.length ? ((questionIndex + 1) / questions.length) * 100 : 0;

    return (
        <main className="page-content quiz-content">
            <div className="page-heading">
                <div><p className="eyebrow">ACTIVE RECALL</p><h1>{playing ? "Vocabulary quiz" : "Quiz"}<span className="heading-period">.</span></h1><p className="page-description">Choose an answer before you see the meaning.</p></div>
                {playing && <button className="button button-quiet study-exit" onClick={() => { setPlaying(false); setError(""); }}><ArrowLeft size={16} /> End quiz</button>}
            </div>

            {error && <div className="inline-error study-error" role="alert"><span>{error}</span>{currentQuestion && currentAnswer?.selectedChoiceId && !currentAnswer.result && <button onClick={() => void submitAnswer(currentQuestion, currentAnswer.selectedChoiceId)}>Retry answer</button>}</div>}

            {playing && currentQuestion && questionSet ? (
                <section className="quiz-session" aria-label="Quiz session">
                    <div className="study-progress-header"><span>Question {questionIndex + 1} / {questions.length}</span><span>{answeredCount} answered</span></div>
                    {questions.length < questionLimit && <p className="study-availability-note" role="status">Only {questions.length} valid {questions.length === 1 ? "question is" : "questions are"} available; you requested {questionLimit}.</p>}
                    {questionSet.limitation === "INSUFFICIENT_CHOICES" && questions.length > 0 && <p className="quiz-availability-detail" role="status">Some words do not have enough unique answers to make four choices, so they were left out.</p>}
                    <div className="study-progress-track" role="progressbar" aria-label="Quiz progress" aria-valuemin={0} aria-valuemax={questions.length} aria-valuenow={questionIndex + 1}><span style={{ width: `${progressPercent}%` }} /></div>
                    <article className="quiz-question">
                        <span className="quiz-direction">{currentQuestion.direction === "KOREAN_TO_VIETNAMESE" ? "KOREAN TO VIETNAMESE" : "VIETNAMESE TO KOREAN"}</span>
                        <h2>{currentQuestion.prompt}</h2>
                        <div className="quiz-choices" role="group" aria-label="Answer choices">
                            {currentQuestion.choices.map((choice, index) => {
                                const selected = currentAnswer?.selectedChoiceId === choice.id;
                                const correct = currentAnswer?.result?.correct_answer === choice.text;
                                const incorrectSelection = selected && currentAnswer?.result && !currentAnswer.result.correct;
                                const choiceClass = [
                                    "quiz-choice",
                                    selected ? "selected" : "",
                                    correct ? "correct" : "",
                                    incorrectSelection ? "incorrect" : "",
                                ].filter(Boolean).join(" ");
                                return (
                                    <button
                                        aria-pressed={selected}
                                        className={choiceClass}
                                        disabled={Boolean(currentAnswer?.selectedChoiceId) || Boolean(submittingToken)}
                                        key={choice.id}
                                        onClick={() => void submitAnswer(currentQuestion, choice.id)}
                                    >
                                        <span className="quiz-choice-letter">{String.fromCharCode(65 + index)}</span>
                                        <span className="quiz-choice-text">{choice.text}</span>
                                        {currentAnswer?.result && correct && <span className="quiz-choice-state">{selected ? "Your answer · Correct" : "Correct answer"}</span>}
                                        {currentAnswer?.result && selected && !currentAnswer.result.correct && <span className="quiz-choice-state">Your answer</span>}
                                        {submittingToken === currentQuestion.question_token && selected && <LoaderCircle className="spin quiz-choice-loader" size={16} />}
                                    </button>
                                );
                            })}
                        </div>
                        {currentAnswer?.result && <div className={`quiz-feedback${currentAnswer.result.correct ? " feedback-correct" : " feedback-incorrect"}`} aria-live="polite">
                            <strong>{currentAnswer.result.correct ? <><Check size={17} /> Correct</> : <><X size={17} /> Not quite</>}</strong>
                            {!currentAnswer.result.correct && <p>Your answer: {currentAnswer.result.selected_answer}</p>}
                            <p><span>Correct answer</span> {currentAnswer.result.correct_answer}</p>
                            {currentAnswer.result.example && <p className="quiz-example" lang="ko">{currentAnswer.result.example}</p>}
                        </div>}
                    </article>
                    <div className="study-navigation">
                        <button className="button button-quiet" disabled={questionIndex === 0 || Boolean(submittingToken)} onClick={() => setQuestionIndex((current) => current - 1)}><ArrowLeft size={16} /> Previous</button>
                        {questionIndex < questions.length - 1
                            ? <button className="button button-primary" disabled={!currentAnswer?.result || Boolean(submittingToken)} onClick={() => { setQuestionIndex((current) => current + 1); setError(""); }}>Next question <ArrowRight size={16} /></button>
                            : <button className="button button-primary" disabled={!currentAnswer?.result || Boolean(submittingToken)} onClick={finishQuiz}><Check size={16} /> Finish quiz</button>}
                    </div>
                </section>
            ) : hasStarted && questionSet ? (
                <section className="study-empty" role="status">
                    <span className="study-empty-mark"><ClipboardCheck size={22} /></span>
                    <h2>{emptyHeading(questionSet.limitation)}</h2>
                    <p>{emptyDescription(questionSet.limitation)}</p>
                    <div className="study-empty-actions">
                        {questionSet.limitation === "NO_VOCABULARY"
                            ? <Link className="button button-primary" href="/vocabulary/new">Add vocabulary <ArrowRight size={16} /></Link>
                            : <button className="button button-quiet" onClick={() => { setCategoryId(""); setLevel(""); setHasStarted(false); }}>Change filters</button>}
                        <button className="text-action" onClick={() => setHasStarted(false)}>Quiz options</button>
                    </div>
                </section>
            ) : (
                <section className="study-setup" aria-labelledby="quiz-options-heading">
                    <div className="study-setup-heading"><span className="study-setup-icon"><ClipboardCheck size={20} /></span><div><p className="eyebrow">SET UP A QUIZ</p><h2 id="quiz-options-heading">Choose your focus</h2></div></div>
                    <div className="study-filter-grid">
                        <label className="study-filter"><span>Category</span><select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">All categories</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name_en}</option>)}</select></label>
                        <label className="study-filter"><span>Level</span><select value={level} onChange={(event) => setLevel(event.target.value)}><option value="">All levels</option><option value="BEGINNER">Beginner</option><option value="INTERMEDIATE">Intermediate</option><option value="ADVANCED">Advanced</option></select></label>
                        <fieldset className="study-count-field"><legend>Questions</legend><div className="study-count-options">{([5, 10, 20] as const).map((count) => <button key={count} type="button" className={questionLimit === count ? "selected" : ""} aria-pressed={questionLimit === count} onClick={() => setQuestionLimit(count)}>{count}</button>)}</div></fieldset>
                    </div>
                    <div className="study-setup-footer"><span>{totalVocabulary === null ? "Loading your wordbook" : `${totalVocabulary} ${totalVocabulary === 1 ? "word" : "words"} in your library`}</span><button className="button button-primary study-start" disabled={setupLoading || starting || totalVocabulary === 0} onClick={() => void startQuiz()}>{starting ? <LoaderCircle className="spin" size={17} /> : <GraduationCap size={17} />}{starting ? "Building quiz" : "Start quiz"}</button></div>
                </section>
            )}
        </main>
    );
}

export function QuizSummary() {
    const [summary, setSummary] = useState<QuizSessionSummary | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let active = true;
        Promise.resolve().then(() => {
            if (!active) return;
            try {
                const stored = window.sessionStorage.getItem(SUMMARY_STORAGE_KEY);
                if (stored) {
                    const parsed: unknown = JSON.parse(stored);
                    if (isQuizSessionSummary(parsed)) setSummary(parsed);
                }
            } catch {
                if (active) setSummary(null);
            }
            if (active) setLoading(false);
        });
        return () => { active = false; };
    }, []);

    if (loading) return <main className="page-content"><div className="table-state" role="status"><LoaderCircle className="spin" size={20} /> Loading quiz summary</div></main>;
    if (!summary) return <main className="page-content"><section className="study-empty"><h2>No recent quiz</h2><p>Start a quiz to see your result.</p><Link className="button button-primary" href="/quiz">Start a quiz <ArrowRight size={16} /></Link></section></main>;

    return (
        <main className="page-content quiz-content">
            <section className="session-summary" aria-labelledby="quiz-summary-heading">
                <span className="summary-check"><Check size={22} /></span>
                <p className="eyebrow">QUIZ COMPLETE</p>
                <h1 id="quiz-summary-heading">Quiz complete<span className="heading-period">.</span></h1>
                <p className="summary-studied">{summary.studied} {summary.studied === 1 ? "question" : "questions"} answered</p>
                <div className="quiz-score"><strong>{summary.correct} / {summary.studied}</strong><span>correct</span></div>
                <div className="summary-actions"><Link className="button button-primary" href="/quiz"><RotateCcw size={16} /> Try again</Link><Link className="button button-quiet" href="/study">Back to learning</Link><Link className="button button-quiet" href="/dashboard">Back to dashboard</Link></div>
            </section>
        </main>
    );
}

function emptyHeading(limitation: QuizQuestionSet["limitation"]): string {
    if (limitation === "NO_VOCABULARY") return "Your wordbook is ready for its first word";
    if (limitation === "INSUFFICIENT_CHOICES") return "Not enough unique answers for a quiz";
    return "No vocabulary matches these filters";
}

function emptyDescription(limitation: QuizQuestionSet["limitation"]): string {
    if (limitation === "NO_VOCABULARY") return "Add at least four words with distinct answers to build a quiz.";
    if (limitation === "INSUFFICIENT_CHOICES") return "Add more vocabulary or change the filters. Quiz choices are never invented.";
    return "Try another category or level.";
}

function isQuizSessionSummary(value: unknown): value is QuizSessionSummary {
    if (typeof value !== "object" || value === null) return false;
    const candidate = value as Record<string, unknown>;
    return Number.isInteger(candidate.studied)
        && Number.isInteger(candidate.correct)
        && (candidate.studied as number) > 0
        && (candidate.correct as number) >= 0
        && (candidate.correct as number) <= (candidate.studied as number);
}