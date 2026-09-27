export type User = { id: number; email: string; created_at: string };
export type Category = { id: number; slug: string; name_ko: string; name_en: string };
export type VocabularyLevel = "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
export const vocabularyLevelLabels: Record<VocabularyLevel, string> = {
    BEGINNER: "Beginner",
    INTERMEDIATE: "Intermediate",
    ADVANCED: "Advanced",
};
export type Vocabulary = {
    id: number;
    word: string;
    meaning: string;
    example: string | null;
    category_id: number;
    category: Category;
    level: VocabularyLevel;
    created_at: string;
    updated_at: string;
};
export type VocabularyInput = {
    word: string;
    meaning: string;
    example: string | null;
    category_id: number;
    level: VocabularyLevel;
};
export type VocabularyPage = { items: Vocabulary[]; page: number; limit: number; total: number; total_pages: number };
export type DashboardStats = {
    total_vocabulary: number;
    by_level: { level: VocabularyLevel; count: number }[];
    categories_used: number;
    by_category: (Category & { count: number })[];
};

export class ApiError extends Error {
    constructor(message: string, readonly status: number) {
        super(message);
        this.name = "ApiError";
    }
}

function resolveApiUrl(configuredUrl: string): string {
    const normalizedUrl = configuredUrl.replace(/\/$/, "");
    if (typeof window === "undefined") return normalizedUrl;

    const apiOrigin = new URL(normalizedUrl, window.location.origin);
    const localHosts = ["localhost", "127.0.0.1"];
    if (localHosts.includes(window.location.hostname) && localHosts.includes(apiOrigin.hostname)) {
        apiOrigin.hostname = window.location.hostname;
    }
    return apiOrigin.origin;
}

const apiUrl = resolveApiUrl(process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000");

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

    let response: Response;
    try {
        response = await fetch(`${apiUrl}${path}`, { ...options, headers, credentials: "include" });
    } catch {
        throw new ApiError("Unable to reach the API. Check that the backend is running.", 0);
    }

    if (response.status === 204) return undefined as T;
    const result: unknown = await response.json().catch(() => null);
    if (!response.ok) {
        const detail = typeof result === "object" && result !== null && "detail" in result
            ? (result as { detail: unknown }).detail
            : null;
        throw new ApiError(typeof detail === "string" ? detail : `Request failed (${response.status}).`, response.status);
    }
    return result as T;
}

export const api = {
    auth: {
        me: () => request<User>("/auth/me"),
        login: (email: string, password: string) => request<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
        register: (email: string, password: string) => request<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
        logout: () => request<void>("/auth/logout", { method: "POST" }),
    },
    categories: () => request<Category[]>("/categories"),
    dashboard: {
        stats: () => request<DashboardStats>("/dashboard/stats"),
    },
    vocabularies: {
        list: (params: URLSearchParams) => request<VocabularyPage>(`/vocabularies?${params.toString()}`),
        get: (id: number) => request<Vocabulary>(`/vocabularies/${id}`),
        create: (data: VocabularyInput) => request<Vocabulary>("/vocabularies", { method: "POST", body: JSON.stringify(data) }),
        update: (id: number, data: VocabularyInput) => request<Vocabulary>(`/vocabularies/${id}`, { method: "PUT", body: JSON.stringify(data) }),
        delete: (id: number) => request<void>(`/vocabularies/${id}`, { method: "DELETE" }),
    },
};