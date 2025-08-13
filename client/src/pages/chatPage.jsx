import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { postQuery, getCurrentUser, getConversations, getConversationDetails } from '../api/chatService';
import { backgroundUploadDocument, getUploadStatus } from '../api/documentService';
import { getWorkspaceDetails  } from '../api/workspaceService';
import { submitFeedback, getConversationFeedback } from '../api/feedbackService';
import Header from '../navigation/headerBar';
import Sidebar from '../navigation/sideBar';
import ModelSelector from '../components/modelSelector';
import './pages.css';

function ChatPage() {
    const { workspaceId } = useParams(); // Get workspaceId from the URL
    const [user, setUser] = useState(null);
    const [workspace, setWorkspace] = useState(null);
    const [conversations, setConversations] = useState([]);
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('');
    const [selectedModel, setSelectedModel] = useState('');
    const [feedbackError, setFeedbackError] = useState('');
    const navigate = useNavigate();
    const messagesEndRef = useRef(null);
    const pollingInterval = useRef(null);

    // Initial data load for the specific workspace
    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            navigate('/');
            return;
        }
        const initialLoad = async () => {
            try {
                // Fetch all data in parallel for speed
                const [userData, workspaceData, convData] = await Promise.all([
                    getCurrentUser(),
                    getWorkspaceDetails(workspaceId),
                    getConversations(workspaceId)
                ]);

                setUser(userData);
                setWorkspace(workspaceData); // <-- Set the workspace state
                setConversations(convData);

                setSelectedModel(userData.selected_model || 'claude-3-5-sonnet-20240620');

                if (convData && convData.length > 0) {
                    await handleSelectConversation(convData[0].id);
                } else {
                    handleNewConversation();
                }
            } catch (error) {
                console.error(error);
                // Don't remove tokens here - let apiClient handle refresh logic
                // Only redirect if it's a true authentication error
                if (error.message.includes('Session expired') || error.message.includes('Please log in again')) {
                    navigate('/');
                }
            }
        };

        if (workspaceId) {
            initialLoad();
        }
    }, [navigate, workspaceId]);
    // Cleanup effect for polling
    useEffect(() => {
        return () => {
            if (pollingInterval.current) clearInterval(pollingInterval.current);
        };
    }, []);

    // Auto-scroll on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSelectConversation = async (convId) => {
        if (isLoading) return;
        setActiveConversationId(convId);
        setIsLoading(true);
        try {
            const [convDetails, feedbackData] = await Promise.all([
                getConversationDetails(convId),
                getConversationFeedback(convId)
            ]);
            
            const feedbackMap = feedbackData.feedback || {};
            
            const formattedMessages = convDetails.messages.flatMap(msg => {
                const userMessage = { sender: 'user', text: msg.query };
                const aiMessage = { sender: 'ai', text: msg.response };
                
                // Check if there's feedback for this AI message
                const messageHash = createMessageHash(msg.query, msg.response);
                if (feedbackMap[messageHash]) {
                    aiMessage.feedback = feedbackMap[messageHash].vote;
                    aiMessage.messageHash = messageHash;
                }
                
                return [userMessage, aiMessage];
            });
            
            setMessages(formattedMessages);
        } catch (error) {
            setMessages([{ sender: 'ai', text: `Error: ${error.message}` }]);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleNewConversation = () => {
        setActiveConversationId(null);
        setMessages([]);
        setInput('');
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = { sender: 'user', text: input };
        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);
        
        const currentInput = input;
        setInput('');
        setIsLoading(true);

        try {
            const chat_history = [];
            for (let i = 0; i < messages.length; i += 2) {
                if (messages[i].sender === 'user' && messages[i+1]?.sender === 'ai') {
                    chat_history.push([messages[i].text, messages[i+1].text]);
                }
            }
            const recent_history = chat_history.slice(-5);

            const response = await postQuery(currentInput, activeConversationId, recent_history, selectedModel, workspaceId);
            
            if (!activeConversationId) {
                setActiveConversationId(response.conversation_id);
                const convData = await getConversations(workspaceId);
                setConversations(convData);
            }
            
            const aiMessage = { sender: 'ai', text: response.answer, sources: response.sources, feedback: null };
            setMessages(prev => [...prev, aiMessage]);

        } catch (error) {
            const errorMessage = { sender: 'ai', text: `Error: ${error.message}` };
            setMessages([...updatedMessages, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file || isUploading) return;

        clearInterval(pollingInterval.current);
        setIsUploading(true);
        setUploadStatus(`Uploading "${file.name}"...`);
        try {
            // Pass workspaceId with the file upload
            const initialResponse = await backgroundUploadDocument(file, workspaceId);
            const { job_id } = initialResponse;

            pollingInterval.current = setInterval(async () => {
                try {
                    const statusResponse = await getUploadStatus(job_id);
                    setUploadStatus(statusResponse.details);
                    if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
                        clearInterval(pollingInterval.current);
                        setIsUploading(false);
                        setTimeout(() => setUploadStatus(''), 5000); 
                    }
                } catch (pollError) {
                    setUploadStatus("Error: Could not get upload status.");
                    clearInterval(pollingInterval.current);
                    setIsUploading(false);
                    setTimeout(() => setUploadStatus(''), 5000);
                }
            }, 3000);

        } catch (uploadError) {
            setUploadStatus(`Error: ${uploadError.message}`);
            setIsUploading(false);
            setTimeout(() => setUploadStatus(''), 5000);
        } finally {
            e.target.value = null; 
        }
    };

// Helper function to create consistent message hash
const createMessageHash = (query, responseText) => {
    const content = `${query}||${responseText}`;
    // Simple hash function (in production, consider using crypto.subtle.digest)
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
        const char = content.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString();
};

const handleFeedback = async (vote, message, query, messageIndex) => {
    if (!query) {
        console.error("Cannot submit feedback without the original query.");
        alert("Could not determine the original question for this feedback.");
        return;
    }
    
    try {
        await submitFeedback(vote, message, query, activeConversationId);
        
        // 更新消息状态，记录反馈
        setMessages(prev => prev.map((msg, index) => {
            if (index === messageIndex) {
                const messageHash = createMessageHash(query, msg.text);
                return { ...msg, feedback: vote, messageHash }; // 1 for like, -1 for dislike
            }
            return msg;
        }));
        
        // Show success message without annoying alert
        console.log('Feedback submitted successfully');
        setFeedbackError(''); // Clear any previous errors
    } catch (error) {
        console.error('Failed to submit feedback:', error);
        // Show error message to user
        const errorMessage = error.message || 'Failed to submit feedback. Please try again.';
        setFeedbackError(errorMessage);
        
        // Clear error after 5 seconds
        setTimeout(() => setFeedbackError(''), 5000);
    }
};

    return (
        <div className="chat-page-layout">
            <Header user={user} workspaceName={workspace?.name} showHomeButton={true} />
            <div className="main-content">
                <Sidebar 
                    conversations={conversations}
                    activeConversationId={activeConversationId}
                    onSelectConversation={handleSelectConversation}
                    onNewConversation={handleNewConversation}
                />
                <div className="chat-area">
                    <div className="chat-container">
                        {messages.length === 0 && !isLoading && (
                             <div className="welcome-message">
                                <h2>{workspace?.name ? `${workspace.name} Workspace` : 'Workspace Ready'}</h2>
                                <p>Upload documents or ask a general question to get started.</p>
                             </div>
                        )}
                    <div className="messages-list">
                        {messages.map((msg, index) => {
                            const originalQuery = msg.sender === 'ai' ? messages[index - 1]?.text : null;
                            const isLatestAiMessage = msg.sender === 'ai' && 
                                index === messages.length - 1 && 
                                !isLoading;
                            
                            return (
                                <div key={index} className={`message ${msg.sender}`}>
                                    <div className="message-bubble">
                                        <p>{msg.text}</p>
                                        
                                        {/* Claude-style feedback: Only show buttons on latest AI message if no feedback given */}
                                        {msg.sender === 'ai' && (
                                            <div className="message-actions">
                                                {msg.feedback ? (
                                                    // Show feedback status for any message that has been rated
                                                    <div className="feedback-status">
                                                        {msg.feedback === 1 ? (
                                                            <span className="feedback-given">👍 Helpful</span>
                                                        ) : (
                                                            <span className="feedback-given">👎 Not helpful</span>
                                                        )}
                                                    </div>
                                                ) : isLatestAiMessage ? (
                                                    // Only show buttons on the latest AI message if not yet rated
                                                    <>
                                                        <button 
                                                            onClick={() => handleFeedback(1, msg, originalQuery, index)} 
                                                            className="feedback-button"
                                                            title="This response was helpful"
                                                        >
                                                            👍
                                                        </button>
                                                        <button 
                                                            onClick={() => handleFeedback(-1, msg, originalQuery, index)} 
                                                            className="feedback-button"
                                                            title="This response was not helpful"
                                                        >
                                                            👎
                                                        </button>
                                                    </>
                                                ) : null}
                                            </div>
                                        )}
                                        
                                        {/* 源引用保持不变 */}
                                        {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && (
                                            <div className="sources">
                                                <strong>Sources:</strong>
                                                <ul>
                                                    {msg.sources.map((source, i) => (
                                                        <li key={i} title={source.content}>
                                                            {source.metadata.source?.split('\\').pop()?.split('/').pop() || 'Uploaded Document'} 
                                                            {source.metadata.page != null && ` (Page: ${source.metadata.page})`}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                        
                        {/* Loading indicator for AI response */}
                        {isLoading && (
                            <div className="message ai">
                                <div className="message-bubble loading">
                                    <div className="typing-indicator">
                                        <div className="typing-dots">
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </div>
                                        <p className="loading-text">AI is analyzing your question and searching through documents...</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                        
                        {/* Model Selector floating inside chat container */}
                        {user?.tier === 'premium' && (
                            <div className="model-selector-float">
                                <ModelSelector 
                                    selectedModel={selectedModel}
                                    onModelChange={setSelectedModel}
                                    disabled={isLoading || isUploading}
                                    user={user}
                                />
                            </div>
                        )}
                    </div>
                    <div className="chat-input-area">
                        {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
                        {feedbackError && <p className="feedback-error">{feedbackError}</p>}
                        <form onSubmit={handleSendMessage} className="chat-form">
                            <label htmlFor="file-upload" className={`file-upload-button ${isUploading ? 'disabled' : ''}`}>
                                📎
                            </label>
                            <input 
                                id="file-upload" 
                                type="file" 
                                accept=".pdf,.md,.txt" 
                                onChange={handleFileUpload} 
                                disabled={isUploading}
                            />
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask a question..."
                                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSendMessage(e); }}
                                disabled={isLoading || isUploading}
                            />
                            <button type="submit" disabled={isLoading || isUploading || !input.trim()}>
                                Send
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ChatPage;