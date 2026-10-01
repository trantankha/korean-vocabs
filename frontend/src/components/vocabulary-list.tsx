"use client";

import { ArrowLeft, ArrowRight, BookOpen, LoaderCircle, Pencil, Plus, Search, SlidersHorizontal, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api, vocabularyLevelLabels, type Category, type Vocabulary, type VocabularyPage } from "@/lib/api";

export function VocabularyList({ initialCategory }: { initialCategory: string }) {
    const router = useRouter();
    const [categories, setCategories] = useState<Category[]>([]);
    const [result, setResult] = useState<VocabularyPage | null>(null);
    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");
    const [categoryId, setCategoryId] = useState(initialCategory);
    const [level, setLevel] = useState("");
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [refreshKey, setRefreshKey] = useState(0);
    const [deleteTarget, setDeleteTarget] = useState<Vocabulary | null>(null);
    const [deleteBusy, setDeleteBusy] = useState(false);

    useEffect(() => {
        const timer = window.setTimeout(() => { setSearch(searchInput.trim()); setPage(1); }, 250);
        return () => window.clearTimeout(timer);
    }, [searchInput]);

    useEffect(() => {
        let active = true;
        api.categories()
            .then((items) => { if (active) setCategories(items); })
            .catch((reason: unknown) => { if (active) setError(reason instanceof Error ? reason.message : "Unable to load categories."); });
        return () => { active = false; };
    }, []);

    useEffect(() => {
        let active = true;
        const params = new URLSearchParams({ page: String(page), limit: "12", sort: "created_at_desc" });
        if (search) params.set("search", search);
        if (categoryId) params.set("category_id", categoryId);
        if (level) params.set("level", level);
        api.vocabularies.list(params)
            .then((pageResult) => {
                if (!active) return;
                setResult(pageResult);
                setError("");
                setLoading(false);
            })
            .catch((reason: unknown) => {
                if (!active) return;
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
                else setError(reason instanceof Error ? reason.message : "Unable to load vocabulary.");
                setLoading(false);
            });
        return () => { active = false; };
    }, [categoryId, level, page, refreshKey, router, search]);

    function changeFilters(change: () => void) {
        setLoading(true);
        change();
    }

    async function confirmDelete() {
        if (!deleteTarget) return;
        setDeleteBusy(true);
        try {
            await api.vocabularies.delete(deleteTarget.id);
            setDeleteTarget(null);
            setLoading(true);
            setRefreshKey((current) => current + 1);
        } catch (reason) {
            if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            else setError(reason instanceof Error ? reason.message : "Unable to delete word.");
        } finally {
            setDeleteBusy(false);
        }
    }

    const items = result?.items ?? [];
    const total = result?.total ?? 0;
    const pageCount = Math.max(result?.total_pages ?? 0, 1);

    return (
        <main className="page-content">
            <div className="page-heading"><div><p className="eyebrow">YOUR KOREAN, GATHERED</p><h1>Word library<span className="heading-period">.</span></h1><p className="page-description">A growing collection, one word at a time.</p></div><Link className="button button-primary add-button" href="/vocabulary/new"><Plus size={18} /> Add a word</Link></div>
            <div className="summary-strip" aria-label="Library summary"><div className="summary-total"><span className="summary-number">{total}</span><span>words found</span></div><span className="summary-divider" /><span className="summary-detail"><span className="summary-korean">단어</span> in this view</span></div>
            <section className="library-section" aria-label="Vocabulary entries">
                <div className="section-heading"><div><h2>All words</h2><span className="result-count">{total} entries</span></div><button className="text-filter" onClick={() => changeFilters(() => { setCategoryId(""); setLevel(""); setSearchInput(""); })}><SlidersHorizontal size={15} /> Clear filters</button></div>
                <div className="toolbar">
                    <label className="search-field"><Search size={18} aria-hidden="true" /><input aria-label="Search Korean words or meanings" onChange={(event) => changeFilters(() => setSearchInput(event.target.value))} placeholder="Search a word or meaning" type="search" value={searchInput} /></label>
                    <label className="select-wrap"><span className="sr-only">Filter by category</span><select onChange={(event) => changeFilters(() => { setCategoryId(event.target.value); setPage(1); })} value={categoryId}><option value="">All categories</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name_en}</option>)}</select></label>
                    <label className="select-wrap level-select"><span className="sr-only">Filter by level</span><select onChange={(event) => changeFilters(() => { setLevel(event.target.value); setPage(1); })} value={level}><option value="">All levels</option>{Object.entries(vocabularyLevelLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
                </div>
                {error && <div className="inline-error" role="alert"><span>{error}</span><button onClick={() => { setLoading(true); setRefreshKey((value) => value + 1); }}>Retry</button></div>}
                <div className="table-wrap"><div className="vocabulary-table" role="table" aria-label="Saved Korean vocabulary">
                    <div className="table-head" role="row"><span role="columnheader">WORD</span><span role="columnheader">MEANING</span><span role="columnheader">CATEGORY</span><span role="columnheader">LEVEL</span><span role="columnheader">ACTIONS</span></div>
                    {loading ? <div className="table-state" role="status"><LoaderCircle className="spin" size={20} /> Loading your words</div> : items.length ? items.map((item) => <VocabularyRow key={item.id} vocabulary={item} onDelete={() => setDeleteTarget(item)} />) : <div className="empty-state"><span className="empty-icon"><BookOpen size={22} /></span><h3>{search || categoryId || level ? "No words match these filters" : "Your wordbook starts here"}</h3><p>{search || categoryId || level ? "Try another search or clear a filter." : "Save a Korean word when you come across one."}</p>{search || categoryId || level ? <button className="text-action" onClick={() => changeFilters(() => { setSearchInput(""); setCategoryId(""); setLevel(""); })}>Clear search and filters</button> : <Link className="button button-secondary" href="/vocabulary/new"><Plus size={16} /> Add your first word</Link>}</div>}
                </div></div>
                <footer className="pagination"><span>Showing {total === 0 ? 0 : (page - 1) * 12 + 1}–{Math.min(page * 12, total)} of {total}</span><div className="page-controls"><button className="page-arrow" disabled={page <= 1 || loading} onClick={() => changeFilters(() => setPage((current) => current - 1))} aria-label="Previous page"><ArrowLeft size={16} /></button><span>Page <strong>{page}</strong> of {pageCount}</span><button className="page-arrow" disabled={page >= pageCount || loading} onClick={() => changeFilters(() => setPage((current) => current + 1))} aria-label="Next page"><ArrowRight size={16} /></button></div></footer>
            </section>
            {deleteTarget && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setDeleteTarget(null); }}><section aria-labelledby="delete-title" aria-modal="true" className="modal-dialog modal-narrow" role="dialog"><div className="delete-symbol"><Trash2 size={19} /></div><h2 id="delete-title" className="dialog-title">Remove this word?</h2><p className="dialog-subtitle">“{deleteTarget.word}” will be deleted from your library.</p><div className="dialog-actions"><button className="button button-quiet" onClick={() => setDeleteTarget(null)}>Keep word</button><button className="button button-danger" disabled={deleteBusy} onClick={confirmDelete}>{deleteBusy ? <LoaderCircle className="spin" size={16} /> : <Trash2 size={16} />}{deleteBusy ? "Removing…" : "Delete word"}</button></div></section></div>}
        </main>
    );
}

function VocabularyRow({ vocabulary, onDelete }: { vocabulary: Vocabulary; onDelete: () => void }) {
    const level = vocabulary.level;
    return <div className="table-row" role="row"><Link className="word-cell" href={`/vocabulary/${vocabulary.id}`} role="cell"><span className="korean-word">{vocabulary.word}</span>{vocabulary.example && <span className="word-example">{vocabulary.example}</span>}</Link><Link className="meaning-cell" href={`/vocabulary/${vocabulary.id}`} role="cell">{vocabulary.meaning}</Link><span className="category-cell" role="cell"><span className="category-mark">{vocabulary.category.name_ko.slice(0, 1)}</span>{vocabulary.category.name_en}</span><span className={`level-cell level-${level.toLowerCase()}`} role="cell"><span />{vocabularyLevelLabels[level]}</span>{vocabulary.is_shared ? <span className="shared-row-label" role="cell">Shared</span> : <div className="row-actions" role="cell"><Link className="icon-button" href={`/vocabulary/${vocabulary.id}/edit`} title="Edit word" aria-label={`Edit ${vocabulary.word}`}><Pencil size={16} /></Link><button className="icon-button danger-icon" onClick={onDelete} title="Delete word" aria-label={`Delete ${vocabulary.word}`}><Trash2 size={16} /></button></div>}</div>;
}