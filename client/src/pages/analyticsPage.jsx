import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUsageStats, getCostSummary } from '../api/analyticsService';
import Header from '../navigation/headerBar';
import './pages.css';

function AnalyticsPage() {
    const [usageStats, setUsageStats] = useState(null);
    const [selectedPeriod, setSelectedPeriod] = useState(30);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            navigate('/');
            return;
        }
        
        loadAnalyticsData();
    }, [navigate, selectedPeriod]);

    const loadAnalyticsData = async () => {
        setLoading(true);
        setError('');
        
        try {
            const [stats] = await Promise.all([
                getUsageStats(selectedPeriod),
                getCostSummary()
            ]);
            
            setUsageStats(stats);
        } catch (err) {
            setError(err.message || 'Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="analytics-page">
                <Header showHomeButton={true} />
                <div className="loading-container">
                    <p>Loading analytics...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="analytics-page">
                <Header showHomeButton={true} />
                <div className="error-container">
                    <h2>Error Loading Analytics</h2>
                    <p>{error}</p>
                    <button onClick={loadAnalyticsData} className="retry-button">
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="analytics-page">
            <Header showHomeButton={true} />
            
            <div className="analytics-container">
                {/* Detailed Usage Stats */}
                {usageStats && usageStats.total_queries > 0 ? (
                    <div className="analytics-content">
                        {/* Overview Stats */}
                        <div className="stats-overview">
                            <div className="overview-header">
                                <h2>📈 Usage Overview ({selectedPeriod} days)</h2>
                                <div className="period-selector">
                                    <button 
                                        className={selectedPeriod === 7 ? 'active' : ''}
                                        onClick={() => setSelectedPeriod(7)}
                                    >
                                        7 Days
                                    </button>
                                    <button 
                                        className={selectedPeriod === 30 ? 'active' : ''}
                                        onClick={() => setSelectedPeriod(30)}
                                    >
                                        30 Days
                                    </button>
                                    <button 
                                        className={selectedPeriod === 90 ? 'active' : ''}
                                        onClick={() => setSelectedPeriod(90)}
                                    >
                                        90 Days
                                    </button>
                                </div>
                            </div>
                            <div className="stats-grid">
                                <div className="stat-item">
                                    <div className="stat-value">{usageStats.total_queries}</div>
                                    <div className="stat-label">Total Queries</div>
                                </div>
                                <div className="stat-item">
                                    <div className="stat-value">{usageStats.total_cost}</div>
                                    <div className="stat-label">Total Cost</div>
                                </div>
                                <div className="stat-item">
                                    <div className="stat-value">{usageStats.success_rate}</div>
                                    <div className="stat-label">Success Rate</div>
                                </div>
                                <div className="stat-item">
                                    <div className="stat-value">{usageStats.avg_cost_per_query}</div>
                                    <div className="stat-label">Avg Cost/Query</div>
                                </div>
                                {usageStats.total_users && (
                                    <div className="stat-item">
                                        <div className="stat-value">{usageStats.total_users}</div>
                                        <div className="stat-label">Active Users</div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* User Usage Breakdown */}
                        {usageStats.user_usage && (
                            <div className="user-usage">
                                <h2>👥 Top Users ({selectedPeriod} days)</h2>
                                <div className="user-stats">
                                    {Object.entries(usageStats.user_usage)
                                        .sort(([,a], [,b]) => b.queries - a.queries)
                                        .slice(0, 10) // Show top 10 users
                                        .map(([userId, stats]) => (
                                        <div key={userId} className="user-card">
                                            <div className="user-header">
                                                <h3>User #{userId}</h3>
                                                <div className="user-cost">{stats.total_cost}</div>
                                            </div>
                                            <div className="user-details">
                                                <p><strong>Queries:</strong> {stats.queries}</p>
                                                <p><strong>Avg Cost:</strong> {stats.avg_cost}</p>
                                                <p><strong>Total Tokens:</strong> {stats.total_tokens?.toLocaleString() || 'N/A'}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Model Usage Breakdown */}
                        <div className="model-usage">
                            <h2>🤖 Model Usage Breakdown ({selectedPeriod} days)</h2>
                            <div className="model-stats">
                                {Object.entries(usageStats.model_usage || {}).map(([model, stats]) => (
                                    <div key={model} className="model-card">
                                        <div className="model-header">
                                            <h3>{model.replace('claude-', 'Claude ')}</h3>
                                        </div>
                                        <div className="model-details">
                                            <p><strong>Queries:</strong> {stats.queries}</p>
                                            <p><strong>Total Cost:</strong> {stats.total_cost}</p>
                                            <p><strong>Avg Cost:</strong> {stats.avg_cost}</p>
                                            <p><strong>Total Tokens:</strong> {stats.total_tokens?.toLocaleString() || 'N/A'}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Daily Cost Trend */}
                        <div className="daily-trend">
                            <h2>📅 Daily Cost Trend ({selectedPeriod} days)</h2>
                            <div className="trend-chart">
                                {Object.entries(usageStats.daily_cost_trend || {})
                                    .sort(([a], [b]) => new Date(a) - new Date(b))
                                    .map(([date, cost]) => (
                                    <div key={date} className="trend-bar">
                                        <div 
                                            className="bar" 
                                            style={{
                                                height: `${Math.max(cost * 1000, 5)}px`, // Scale for visibility
                                                minHeight: '5px'
                                            }}
                                        ></div>
                                        <div className="bar-label">{new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                                        <div className="bar-value">${cost.toFixed(4)}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                    </div>
                ) : (
                    <div className="no-data">
                        <h2>📊 No Usage Data</h2>
                        <p>You haven&rsquo;t made any queries in the selected period.</p>
                        <button 
                            onClick={() => navigate('/dashboard')} 
                            className="start-chat-button"
                        >
                            Start Chatting
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AnalyticsPage;