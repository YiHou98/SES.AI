import { useNavigate, Link } from 'react-router-dom';
import PropTypes from 'prop-types'; 
import './navigation.css';

function Header({ user }) {
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        navigate('/');
    };

    const handleHomeClick = () => {
        navigate('/dashboard');
    };

    return (
        <header className="app-header">
            <div className="header-content">
                <div className="header-left">
           
                        <button className="home-button" onClick={handleHomeClick} title="Back to Dashboard">
                            🏠
                        </button>
                    
                    <h1 className="app-title">
                        RAG Q&A System
    
                    </h1>
                </div>
                {user && (
                    <div className="user-info">
                        <span>Welcome, {user.username}</span>
                        <Link to="/subscription" className="user-tier-link">
                            <span className={`user-tier ${user.tier}`}>{user.tier}</span>
                        </Link>
                        <button onClick={handleLogout} className="logout-button">Logout</button>
                    </div>
                )}
            </div>
        </header>
    );
}

Header.propTypes = {
  user: PropTypes.shape({
    username: PropTypes.string,
    tier: PropTypes.string
  })
};

Header.defaultProps = {
  user: null
};

export default Header;