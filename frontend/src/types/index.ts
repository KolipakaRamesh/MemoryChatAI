export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
}

export interface ChatMessageResponse {
    response: string;
    conversation_id: string;
    message_id: string;
    observability: ObservabilityData;
}

export interface ObservabilityData {
    request_id: string;
    short_term_memory: {
        messages: {
            id: string;
            role: string;
            content: string;
            tokens: number;
            timestamp: string;
            includedInPrompt: boolean;
        }[];
        summary: string | null;
    };
    long_term_memory: {
        preferences: Record<string, any>;
        behavior_patterns: Record<string, any>;
        context: Record<string, any>;
        last_updated: string;
    };
    semantic_memory: {
        relevant_memories: {
            content: string;
            metadata: Record<string, any>;
        }[];
    };
    feedback_memory: {
        corrections: any[];
    };
    token_usage: {
        total: number;
        estimated_response: number;
        cost: number;
        breakdown: Record<string, number>;
    };
    request_trace: {
        steps: {
            name: string;
            latency_ms: number;
        }[];
        total_latency_ms: number;
    };
}
