"use client";

import { ArrowLeft, LoaderCircle, Pencil, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api, vocabularyLevelLabels, type Vocabulary } from "@/lib/api";

export function VocabularyDetail({ vocabularyId }: { vocabularyId: string }) {
    const router = useRouter();
    const [vocabulary, setVocabulary] = useState<Vocabulary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [confirmingDelete, setConfirmingDelete] = useState(false);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        let active = true;
        api.vocabularies.get(Number(vocabularyId))
            .then((item) => { if (active) setVocabulary(item); })
            .catch((reason: unknown) => {
                if (!active) return;
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
                else setError(reason instanceof Error ? reason.message : "Unable to load this word.");
            })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, [router, vocabularyId]);

    async function deleteWord() {
        if (!vocabulary) return;
        setDeleting(true);
        try {
            await api.vocabularies.delete(vocabulary.id);
            router.replace("/vocabulary");
            router.refresh();
        } catch (reason) {
            if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            else setError(reason instanceof Error ? reason.message : "Unable to delete this word.");
            setConfirmingDelete(false);
        } finally {
            setDeleting(false);
        }
    }

    if (loading) return <main className="page-content"><div className="table-state" role="status"><LoaderCircle className="spin" size={20} /> Loading word details</div></main>;
    if (error && !vocabulary) return <main className="page-content"><div className="inline-error" role="alert"><span>{error}</span><Link href="/vocabulary">Back to word library</Link></div></main>;
    if (!vocabulary) return null;

    return (
        <main className="page-content detail-page">
            <Link className="back-link" href="/vocabulary"><ArrowLeft size={16} /> Back to word library</Link>
            <div className="detail-page-heading"><div><p className="eyebrow">WORD CARD</p><span className={`level-cell detail-level level-${vocabulary.level.toLowerCase()}`}><span />{vocabularyLevelLabels[vocabulary.level]}</span><h1>{vocabulary.word}<span className="heading-period">.</span></h1><p className="detail-page-meaning">{vocabulary.meaning}</p></div><div className="detail-page-actions"><Link className="button button-primary" href={`/vocabulary/${vocabulary.id}/edit`}><Pencil size={16} /> Edit word</Link><button className="icon-button danger-icon" onClick={() => setConfirmingDelete(true)} title="Delete word" aria-label="Delete word"><Trash2 size={17} /></button></div></div>
            {error && <div className="inline-error" role="alert"><span>{error}</span></div>}
            {vocabulary.example && <section className="detail-example"><p className="eyebrow">EXAMPLE SENTENCE</p><p>{vocabulary.example}</p></section>}
            <div className="detail-page-category"><span className="category-mark">{vocabulary.category.name_ko.slice(0, 1)}</span><span>{vocabulary.category.name_ko} · {vocabulary.category.name_en}</span></div>
            {confirmingDelete && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setConfirmingDelete(false); }}><section aria-labelledby="delete-title" aria-modal="true" className="modal-dialog modal-narrow" role="dialog"><div className="delete-symbol"><Trash2 size={19} /></div><h2 id="delete-title" className="dialog-title">Remove this word?</h2><p className="dialog-subtitle">“{vocabulary.word}” will be deleted from your library.</p><div className="dialog-actions"><button className="button button-quiet" onClick={() => setConfirmingDelete(false)}>Keep word</button><button className="button button-danger" disabled={deleting} onClick={deleteWord}>{deleting ? <LoaderCircle className="spin" size={16} /> : <Trash2 size={16} />}{deleting ? "Removing…" : "Delete word"}</button></div></section></div>}
        </main>
    );
}