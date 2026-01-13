// src/types/index.ts

export interface User {
    id: number;
    username: string;
    english_level: string;  // A1-C2
    learning_goal?: string;
    interests?: Record<string, number>;
}

export interface Article {
    id: number;
    title: string;
    content?: string;
    summary?: string;
    category: string;
    difficulty_level: string;
    word_count: number;
    source: string;
    source_name?: string;
    imageUrl?: string;
    readTimeMin?: number;
    created_at?: string;
}

export interface ArticleAnalysis {
    articleId: number;
    highlights: HighlightItem[];
}

export interface HighlightItem {
    id: string;
    text: string;
    type: 'vocabulary' | 'collocation' | 'grammar';
    explanation: string;
    translation?: string;
    anchors?: string[];  // 精确匹配锚点
}

export interface VocabularyItem {
    id?: number;
    word: string;
    definition?: string;
    pronunciation?: string;
    cefr?: string;
    source_article_id?: number;
    created_at?: string;
}

export interface ReadingHistory {
    id: number;
    article_id: number;
    title: string;
    completion_rate: number;
    time_spent: number;
    created_at: string;
}

export interface UserStats {
    total_articles: number;
    total_time_minutes: number;
    avg_completion_rate: number;
    vocabulary_count: number;
    category_distribution: Record<string, number>;
}

export type ViewType = 'discover' | 'library' | 'history' | 'vocabulary' | 'stats';
