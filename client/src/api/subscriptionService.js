import { apiClient } from './apiClient';

const API_BASE_URL = 'http://localhost:8000/api/v1/subscriptions';

export const upgradeToPremium = async () => {
    const response = await apiClient(`${API_BASE_URL}/upgrade`, {
        method: 'POST'
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upgrade subscription.');
    }
    return response.json();
};

export const cancelSubscription = async () => {
    const response = await apiClient(`${API_BASE_URL}/cancel`, {
        method: 'POST'
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to cancel subscription.');
    }
    return response.json();
};