import { apiClient } from './apiClient';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const postQuery = async (query, conversation_id, chat_history, model, workspaceId) => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        throw new Error("No access token found. Please log in again.");
    }
    
    // Include workspace_id in the request body for the chat endpoint
    const body = { query, conversation_id, chat_history, model, workspace_id: workspaceId };

    const response = await apiClient(`${API_BASE_URL}/chat`, {
        method: 'POST',
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorData = await response.json();
        const detail = errorData.detail?.[0]?.msg || errorData.detail || 'Failed to get response';
        throw new Error(detail);
    }
    return response.json();
};

export const getCurrentUser = async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        throw new Error("No access token found. Please log in again.");
    }

    const response = await apiClient(`${API_BASE_URL}/auth/me`, {
        method: 'GET'
    });

    if (!response.ok) {
        throw new Error('Failed to fetch user data.');
    }
    return response.json();
};

// --- THIS IS THE CORRECTED FUNCTION ---
export const getConversations = async (workspaceId) => { // <-- FIX: Add workspaceId as a parameter
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error("No access token found.");

    const response = await apiClient(`${API_BASE_URL}/conversations/?workspace_id=${workspaceId}`, {
        method: 'GET'
    });
    
    if (!response.ok) throw new Error('Failed to fetch conversations.');
    return response.json();
};

export const getConversationDetails = async (conversationId) => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error("No access token found.");

    const response = await apiClient(`${API_BASE_URL}/conversations/${conversationId}`, {
        method: 'GET'
    });
    
    if (!response.ok) throw new Error('Failed to fetch conversation details.');
    return response.json();
};