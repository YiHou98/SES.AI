import { apiClient } from './apiClient';

const API_BASE_URL = 'http://localhost:8000/api/v1/feedback';

export const submitFeedback = async (vote, message, query, conversationId = null) => {
    const payload = {
        vote: vote,
        query: query,
        response_text: message.text,
        source_documents: message.sources || [],
        conversation_id: conversationId
    };

    const response = await apiClient(API_BASE_URL, {
        method: 'POST',
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        // Parse error message from backend and throw it
        const errorData = await response.json();
        const errorMessage = errorData.detail || 'Failed to submit feedback';
        throw new Error(errorMessage);
    }
    return response.status === 204; // Return true on success
};

export const checkFeedbackExists = async (query, responseText) => {
    const params = new URLSearchParams({
        query: query,
        response_text: responseText
    });

    const response = await apiClient(`${API_BASE_URL}/check?${params}`, {
        method: 'GET'
    });

    if (response.ok) {
        return await response.json();
    }
    return { has_feedback: false };
};

export const getConversationFeedback = async (conversationId) => {
    const response = await apiClient(`${API_BASE_URL}/conversation/${conversationId}`, {
        method: 'GET'
    });

    if (response.ok) {
        return await response.json();
    }
    return { feedback: {} };
};