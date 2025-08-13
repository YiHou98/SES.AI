import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/landingPage';
import DashboardPage from './pages/dashboardPage';
import ChatPage from './pages/chatPage';
import SubscriptionPage from './pages/subscriptionPage';
import AnalyticsPage from './pages/analyticsPage';
function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/workspace/:workspaceId/chat" element={<ChatPage />} />
          <Route path="/subscription" element={<SubscriptionPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;