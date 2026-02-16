import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const chatApi = {
    sendMessage: async (message: string, conversationId?: string) => {
        const response = await apiClient.post('/chat/', {
            message,
            conversation_id: conversationId,
        });
        return response.data;
    },

    getConversations: async () => {
        const response = await apiClient.get('/chat/conversations');
        return response.data;
    },

    getMemoryProfile: async () => {
        const response = await apiClient.get('/memory/profile');
        return response.data;
    }
};

export default apiClient;
