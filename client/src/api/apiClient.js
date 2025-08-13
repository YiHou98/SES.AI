import { refreshAccessToken } from './authService';

/**
 * Enhanced fetch that automatically handles token refresh on 401 errors
 */
export const apiClient = async (url, options = {}) => {
    const makeRequest = async (token) => {
        const headers = {
            ...options.headers,
        };
        
        // Only add Content-Type if not FormData (for file uploads)
        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }
        
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }
        
        return fetch(url, {
            ...options,
            headers,
        });
    };

    // First attempt with existing token
    let token = localStorage.getItem('accessToken');
    let response = await makeRequest(token);

    // If 401, try refreshing token once
    if (response.status === 401 && token) {
        try {
            token = await refreshAccessToken();
            response = await makeRequest(token);
        } catch (refreshError) {
            // If refresh fails, redirect to login
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            window.location.href = '/';
            throw new Error('Session expired. Please log in again.');
        }
    }

    return response;
};

/**
 * Helper to get auth headers
 */
export const getAuthHeaders = () => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error("No access token found.");
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
};