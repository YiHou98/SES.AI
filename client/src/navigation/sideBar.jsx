import PropTypes from 'prop-types';
import './navigation.css';

function Sidebar({ conversations, onSelectConversation, activeConversationId, onNewConversation }) {
    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <h2>Conversations</h2>
                <button onClick={onNewConversation} className="new-chat-button">+</button>
            </div>
            <div className="conversation-list">
                {conversations.map(conv => (
                    <div
                        key={conv.id}
                        className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
                        onClick={() => onSelectConversation(conv.id)}
                    >
                        {conv.title}
                    </div>
                ))}
            </div>
        </div>
    );
}

Sidebar.propTypes = {
  conversations: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    title: PropTypes.string
  })).isRequired,
  onSelectConversation: PropTypes.func.isRequired,
  activeConversationId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onNewConversation: PropTypes.func.isRequired
};

Sidebar.defaultProps = {
  activeConversationId: null
};

export default Sidebar;