"use client";

import { ArrowLeft, Check, ChevronDown, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { ApiError, api, vocabularyLevelLabels, type Category, type Vocabulary, type VocabularyInput, type VocabularyLevel } from "@/lib/api";

export function VocabularyForm({ vocabularyId }: { vocabularyId?: string }) {
    const router = useRouter();
    const [categories, setCategories] = useState<Category[]>([]);
    const [initial, setInitial] = useState<Vocabulary | null>(null);
    const [word, setWord] = useState("");
    const [meaning, setMeaning] = useState("");
    const [example, setExample] = useState("");
    const [exampleEn, setExampleEn] = useState("");
    const [categoryId, setCategoryId] = useState("");
    const [level, setLevel] = useState<VocabularyLevel>("BEGINNER");
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const isEditing = Boolean(vocabularyId);

    useEffect(() => {
        let active = true;
        const vocabularyRequest = vocabularyId ? api.vocabularies.get(Number(vocabularyId)) : Promise.resolve(null);
        Promise.all([api.categories(), vocabularyRequest])
            .then(([availableCategories, vocabulary]) => {
                if (!active) return;
                if (vocabulary?.is_shared) {
                    router.replace(`/vocabulary/${vocabulary.id}`);
                    return;
                }
                setCategories(availableCategories);
                setInitial(vocabulary);
                setWord(vocabulary?.word ?? "");
                setMeaning(vocabulary?.meaning ?? "");
                setExample(vocabulary?.example ?? "");
                setExampleEn(vocabulary?.example_en ?? "");
                setCategoryId(String(vocabulary?.category_id ?? availableCategories[0]?.id ?? ""));
                setLevel(vocabulary?.level ?? "BEGINNER");
                setLoading(false);
            })
            .catch((reason: unknown) => {
                if (!active) return;
                if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
                else setError(reason instanceof Error ? reason.message : "Unable to load the form.");
                setLoading(false);
            });
        return () => { active = false; };
    }, [router, vocabularyId]);

    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");
        setBusy(true);
        const data: VocabularyInput = { word: word.trim(), meaning: meaning.trim(), example: example.trim() || null, example_en: exampleEn.trim() || null, category_id: Number(categoryId), level };
        try {
            const saved = isEditing && vocabularyId
                ? await api.vocabularies.update(Number(vocabularyId), data)
                : await api.vocabularies.create(data);
            router.push(isEditing ? `/vocabulary/${saved.id}` : "/vocabulary");
            router.refresh();
        } catch (reason) {
            if (reason instanceof ApiError && reason.status === 401) router.replace("/login");
            else setError(reason instanceof Error ? reason.message : "Unable to save this word.");
        } finally {
            setBusy(false);
        }
    }

    if (loading) return <main className="page-content"><div className="table-state" role="status"><LoaderCircle className="spin" size={20} /> Loading word details</div></main>;
    if (error && isEditing && !initial) return <main className="page-content"><div className="inline-error" role="alert"><span>{error}</span><Link href="/vocabulary">Back to word library</Link></div></main>;

    return (
        <main className="page-content">
            <Link className="back-link" href={initial ? `/vocabulary/${initial.id}` : "/vocabulary"}><ArrowLeft size={16} /> Back to {initial ? "word details" : "word library"}</Link>
            <div className="form-page-heading"><p className="eyebrow">WORD DETAILS</p><h1>{initial ? "Edit this word" : "Add a Korean word"}<span className="heading-period">.</span></h1><p className="page-description">Keep the meaning clear. Add an example when it helps.</p></div>
            <form className="route-form" onSubmit={submit}>
                <label htmlFor="word">Korean word</label>
                <input autoFocus id="word" maxLength={200} onChange={(event) => setWord(event.target.value)} placeholder="예: 학교" required value={word} />
                <label htmlFor="meaning">Meaning</label>
                <input id="meaning" maxLength={10000} onChange={(event) => setMeaning(event.target.value)} placeholder="School" required value={meaning} />
                <label htmlFor="example">Example sentence <span className="optional-label">OPTIONAL</span></label>
                <textarea id="example" maxLength={10000} onChange={(event) => setExample(event.target.value)} placeholder="저는 학교에 가요." rows={4} value={example} />
                <label htmlFor="example-en">English example translation <span className="optional-label">OPTIONAL</span></label>
                <textarea id="example-en" maxLength={10000} onChange={(event) => setExampleEn(event.target.value)} placeholder="I go to school." rows={3} value={exampleEn} />
                <div className="form-select-grid">
                    <div><label htmlFor="category">Category</label><div className="form-select-wrap"><select id="category" onChange={(event) => setCategoryId(event.target.value)} required value={categoryId}><option disabled value="">Select a category</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name_ko} · {category.name_en}</option>)}</select><ChevronDown size={15} /></div></div>
                    <div><label htmlFor="level">Level</label><div className="form-select-wrap"><select id="level" onChange={(event) => setLevel(event.target.value as VocabularyLevel)} value={level}>{Object.entries(vocabularyLevelLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select><ChevronDown size={15} /></div></div>
                </div>
                {error && <p className="form-error" role="alert">{error}</p>}
                <div className="route-form-actions"><Link className="button button-quiet" href={initial ? `/vocabulary/${initial.id}` : "/vocabulary"}>Cancel</Link><button className="button button-primary" disabled={busy || categories.length === 0} type="submit">{busy ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />}{busy ? "Saving…" : initial ? "Save changes" : "Save word"}</button></div>
            </form>
        </main>
    );
}