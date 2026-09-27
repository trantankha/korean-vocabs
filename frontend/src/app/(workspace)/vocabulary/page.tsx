import { VocabularyList } from "@/components/vocabulary-list";

export default async function VocabularyPage({ searchParams }: { searchParams: Promise<{ category_id?: string }> }) {
    const { category_id: categoryId = "" } = await searchParams;
    return <VocabularyList initialCategory={categoryId} />;
}