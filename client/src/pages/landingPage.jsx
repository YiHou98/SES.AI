import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser, registerUser } from '../api/authService';
import { getCurrentUser } from '../api/chatService'; // Import getCurrentUser
import './pages.css'; // Assuming you have this CSS file

function LandingPage() {
    const navigate = useNavigate();

    // --- THIS IS THE UPDATED LOGIC ---
    // On component mount, we'll try to fetch the user's data.
    // If it succeeds, it means they have a valid HttpOnly refresh token cookie,
    // and the apiClient will handle getting a new access token.
    useEffect(() => {
        const checkForActiveSession = async () => {
            try {
                // Try to get user data. If this succeeds, the user is logged in.
                await getCurrentUser();
                navigate('/dashboard'); // Redirect to dashboard if session is valid
            } catch (error) {
                // If it fails, do nothing. The user needs to log in.
                console.log("No active session found. Please log in.");
            }
        };
        checkForActiveSession();
    }, [navigate]);
    // --- END OF UPDATED LOGIC ---

    // State to toggle between Login and Register views
    const [isLoginMode, setIsLoginMode] = useState(true);

    // Form fields state
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    // UI feedback state
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError(null);

        try {
            if (isLoginMode) {
                // loginUser now handles setting the in-memory access token
                await loginUser(email, password);
                navigate('/dashboard'); 
            } else {
                await registerUser(username, email, password);
                alert('Registration successful! Please log in.');
                setIsLoginMode(true);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const toggleMode = () => {
        setIsLoginMode(!isLoginMode);
        setError(null);
    };

    return (
        <div className="landing-container">
            <div className="form-box">
                <h2>{isLoginMode ? 'Login' : 'Register'}</h2>
                <form onSubmit={handleSubmit}>
                    {!isLoginMode && (
                        <div className="input-group">
                            <label htmlFor="username">Username</label>
                            <input
                                type="text"
                                id="username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                        </div>
                    )}
                    <div className="input-group">
                        <label htmlFor="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    {error && <p className="error-message">{error}</p>}
                    <button type="submit" className="submit-button" disabled={loading}>
                        {loading ? 'Processing...' : (isLoginMode ? 'Login' : 'Create Account')}
                    </button>
                </form>
                <p className="toggle-link" onClick={toggleMode}>
                    {isLoginMode
                        ? "Don't have an account? Register"
                        : 'Already have an account? Login'}
                </p>
            </div>
        </div>
    );
}

export default LandingPage;