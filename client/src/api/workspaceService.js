import { apiClient } from './apiClient';

const API_BASE_URL = 'http://localhost:8000/api/v1/workspaces';

export const getWorkspaces = async () => {
    const response = await apiClient(API_BASE_URL, {
        method: 'GET'
    });
    if (!response.ok) throw new Error('Failed to fetch workspaces.');
    return response.json();
};

export const createWorkspace = async (name, domain) => {
    const response = await apiClient(API_BASE_URL, {
        method: 'POST',
        body: JSON.stringify({ name, domain }),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create workspace.');
    }
    return response.json();
};

export const getWorkspaceDetails = async (workspaceId) => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error("No access token found.");

    const response = await apiClient(`${API_BASE_URL}/${workspaceId}`, {
        method: 'GET'
    });
    if (!response.ok) throw new Error('Failed to fetch workspace details.');
    return response.json();
};