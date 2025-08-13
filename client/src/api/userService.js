import { apiClient } from './apiClient';

const API_BASE_URL = 'http://localhost:8000/api/v1/users';

export const updateUserModel = async (model) => {
    const response = await apiClient(`${API_BASE_URL}/me/model?model=${model}`, {
        method: 'POST'
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update model.');
    }
    return response.json();
};