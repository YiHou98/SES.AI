import { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import './modelSelector.css';

const ModelSelector = ({ selectedModel, onModelChange, disabled, user }) => {
    const [showDropdown, setShowDropdown] = useState(false);
    const selectorRef = useRef(null);

    // Model options configuration
    const modelOptions = [
        { 
            value: 'claude-3-5-sonnet-20240620', 
            label: 'Claude 3.5 Sonnet',
            description: 'Most intelligent model'
        },
        { 
            value: 'claude-3-opus-20240229', 
            label: 'Claude 3 Opus',
            description: 'Powerful model for complex tasks'
        },
    ];

    // Handle click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (selectorRef.current && !selectorRef.current.contains(event.target)) {
                setShowDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleModelSelect = (modelValue) => {
        onModelChange(modelValue);
        setShowDropdown(false);
    };

    const getCurrentModelLabel = () => {
        const model = modelOptions.find(m => m.value === selectedModel);
        return model ? model.label : 'Select Model';
    };

    // Only render for premium users
    if (user?.tier !== 'premium') {
        return null;
    }

    return (
        <div className="model-selector-wrapper" ref={selectorRef}>
            <button 
                className="model-selector-trigger"
                onClick={() => setShowDropdown(!showDropdown)}
                disabled={disabled}
                type="button"
            >
                <span className="model-icon">🤖</span>
                <span className="model-name">{getCurrentModelLabel()}</span>
                <span className="dropdown-arrow">▼</span>
            </button>
            
            {showDropdown && (
                <div className="model-selector-dropdown">
                    {modelOptions.map((model) => (
                        <div
                            key={model.value}
                            className={`model-option ${selectedModel === model.value ? 'selected' : ''}`}
                            onClick={() => handleModelSelect(model.value)}
                        >
                            <div className="model-option-header">
                                <span className="model-option-name">{model.label}</span>
                                {selectedModel === model.value && <span className="check-mark">✓</span>}
                            </div>
                            <span className="model-option-description">{model.description}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

ModelSelector.propTypes = {
  selectedModel: PropTypes.string.isRequired,
  onModelChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  user: PropTypes.shape({
    tier: PropTypes.string
  })
};

ModelSelector.defaultProps = {
  disabled: false,
  user: null
};

export default ModelSelector;