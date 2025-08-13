import { apiClient } from './apiClient';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const getUsageStats = async (days = 30) => {
    const response = await apiClient(`${API_BASE_URL}/analytics/usage?days=${days}`, {
        method: 'GET'
    });
    
    if (!response.ok) {
        throw new Error('Failed to fetch usage statistics');
    }
    return response.json();
};

export const getCostSummary = async () => {
    const response = await apiClient(`${API_BASE_URL}/analytics/cost-summary`, {
        method: 'GET'
    });
    
    if (!response.ok) {
        throw new Error('Failed to fetch cost summary');
    }
    return response.json();
};