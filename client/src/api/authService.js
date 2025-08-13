const API_BASE_URL = 'http://localhost:8000/api/v1/auth';

/**
 * Handles the login API call.
 */
export const loginUser = async (email, password) => {
    // Basic input validation
    if (!email || !password) {
        throw new Error('Email and password are required');
    }
    if (!email.includes('@')) {
        throw new Error('Please enter a valid email address');
    }
    if (password.length < 6) {
        throw new Error('Password must be at least 6 characters');
    }

    const formData = new URLSearchParams();
    formData.append('username', email); // The backend expects 'username' for the email
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
    }
    
    const data = await response.json();
    // Store both tokens in localStorage for future API calls
    localStorage.setItem('accessToken', data.access_token);
    localStorage.setItem('refreshToken', data.refresh_token);
    return data;
};

/**
 * Handles the registration API call.
 */
export const registerUser = async (username, email, password) => {
    // Basic input validation
    if (!username || !email || !password) {
        throw new Error('Username, email, and password are required');
    }
    if (!email.includes('@')) {
        throw new Error('Please enter a valid email address');
    }
    if (password.length < 6) {
        throw new Error('Password must be at least 6 characters');
    }
    if (username.length < 3) {
        throw new Error('Username must be at least 3 characters');
    }

    const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
    }
    return response.json();
};

/**
 * Logs out the user by clearing tokens and redirecting to login
 */
export const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/';
};

/**
 * Refreshes the access token using the stored refresh token.
 */
export const refreshAccessToken = async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
        throw new Error('No refresh token found. Please log in again.');
    }

    const response = await fetch(`${API_BASE_URL}/refresh`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${refreshToken}` 
        }
    });

    if (!response.ok) {
        // If refresh fails, clear tokens and throw error
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        throw new Error('Session expired. Please log in again.');
    }

    const data = await response.json();
    // Update both tokens
    localStorage.setItem('accessToken', data.access_token);
    localStorage.setItem('refreshToken', data.refresh_token);
    return data.access_token;
};