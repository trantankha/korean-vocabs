import { VocabularyDetail } from "@/components/vocabulary-detail";

export default async function VocabularyDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    return <VocabularyDetail vocabularyId={id} />;
}