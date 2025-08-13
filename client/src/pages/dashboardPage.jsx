import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../navigation/headerBar';
import { getCurrentUser } from '../api/chatService';
import { getWorkspaces, createWorkspace } from '../api/workspaceService';
import './pages.css';

function DashboardPage() {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [workspaces, setWorkspaces] = useState([]);
    const [newTopic, setNewTopic] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const fetchWorkspacesData = async () => {
        try {
            const workspacesData = await getWorkspaces();
            setWorkspaces(workspacesData);
        } catch (error) {
            console.error("Failed to fetch workspaces:", error);
        }
    };

    useEffect(() => {
        const initialLoad = async () => {
            try {
                const userData = await getCurrentUser();
                setUser(userData);
                await fetchWorkspacesData();
            } catch (error) {
                console.error("Failed to load initial data:", error);
                navigate('/');
            }
        };
        initialLoad();
    }, [navigate]);

    const handleWorkspaceClick = (workspaceId) => {
        navigate(`/workspace/${workspaceId}/chat`);
    };

    const handleCreateWorkspace = async (name) => {
        const trimmedName = name.trim();
        if (!trimmedName) {
            alert("Please enter a topic name.");
            return;
        }

        // New check to prevent duplicates
        const isDuplicate = workspaces.some(
            ws => ws.name.toLowerCase() === trimmedName.toLowerCase()
        );

        if (isDuplicate) {
            alert(`A workspace named "${trimmedName}" already exists.`);
            return; // Stop the creation process
        }

        setIsLoading(true);
        try {
            const newWorkspace = await createWorkspace(trimmedName, "General");
            navigate(`/workspace/${newWorkspace.id}/chat`);
        } catch (error) {
            alert(`Failed to create workspace: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFormSubmit = (e) => {
        e.preventDefault();
        handleCreateWorkspace(newTopic);
    };

    return (
        <div className="dashboard-layout">
            <Header user={user} />
            <div className="dashboard-container">
                <div className="dashboard-box">
                    <p className="quick-start-title">Create a Custom Workspace</p>
                    
                    <form className="create-workspace-form" onSubmit={handleFormSubmit}>
                        <div className="form-inputs">
                            <input 
                                type="text" 
                                placeholder="Enter Topic Name (e.g., R&D Materials, Market Research)" 
                                value={newTopic}
                                onChange={(e) => setNewTopic(e.target.value)}
                            />
                        </div>
                        <button type="submit" className="create-button" disabled={isLoading}>
                            {isLoading ? 'Creating...' : '+ Create Workspace'}
                        </button>
                    </form>

                    <div className="recent-workspaces">
                        <h3>All Workspaces</h3>
                        {workspaces.length === 0 ? (
                            <p className="no-workspaces">No workspaces yet. Create one to get started!</p>
                        ) : (
                            <ul>
                                {workspaces.map(ws => (
                                    <li key={ws.id} onClick={() => handleWorkspaceClick(ws.id)}>
                                        {ws.name} ({ws.documents.length} docs)
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardPage;