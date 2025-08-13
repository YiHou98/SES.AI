import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser } from '../api/chatService';
import { upgradeToPremium, cancelSubscription } from '../api/subscriptionService';
import Header from '../navigation/headerBar';
import './pages.css';

function SubscriptionPage() {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const userData = await getCurrentUser();
                setUser(userData);
            } catch (error) {
                navigate('/');
            }
        };
        fetchUser();
    }, [navigate]);

    const handleUpgrade = async () => {
        setIsLoading(true);
        setMessage('');
        try {
            const updatedUser = await upgradeToPremium();
            setUser(updatedUser);
            setMessage('Successfully upgraded to Premium!');
        } catch (error) {
            setMessage(`Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCancel = async () => {
        setIsLoading(true);
        setMessage('');
        try {
            const updatedUser = await cancelSubscription();
            setUser(updatedUser);
            setMessage('Subscription successfully cancelled.');
        } catch (error) {
            setMessage(`Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };
    
    if (!user) {
        return <div>Loading...</div>; // Or a spinner component
    }

    const isPremium = user.tier === 'premium';

    return (
        <div className="subscription-page-layout">
            <Header user={user}/>
            <div className="subscription-container">
                <div className="subscription-box">
                    <h2>Subscription Management</h2>
                    <p>You are currently on the <strong>{isPremium ? 'Premium' : 'Free'}</strong> plan.</p>
                    
                    <div className="plan-details">
                        <h3>{isPremium ? 'Premium Plan Benefits' : 'Free Plan Limits'}</h3>
                        <ul>
                            <li>{isPremium ? 'Unlimited questions' : '10 questions per day'}</li>
                            <li>{isPremium ? 'Access to the most powerful models' : 'Standard model access'}</li>
                            <li>{isPremium ? 'Priority support' : 'Community support'}</li>
                        </ul>
                    </div>

                    {isPremium ? (
                        <button onClick={handleCancel} disabled={isLoading} className="cancel-button">
                            {isLoading ? 'Cancelling...' : 'Cancel Subscription'}
                        </button>
                    ) : (
                        <button onClick={handleUpgrade} disabled={isLoading} className="upgrade-button">
                            {isLoading ? 'Upgrading...' : 'Upgrade to Premium'}
                        </button>
                    )}

                    {message && <p className="status-message">{message}</p>}
                </div>
            </div>
        </div>
    );
}

export default SubscriptionPage;