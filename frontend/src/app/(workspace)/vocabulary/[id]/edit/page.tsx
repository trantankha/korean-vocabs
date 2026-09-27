import { VocabularyForm } from "@/components/vocabulary-form";

export default async function EditVocabularyPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    return <VocabularyForm vocabularyId={id} />;
}