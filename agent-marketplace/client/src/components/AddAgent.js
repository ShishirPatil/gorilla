import React, { useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import UserContext from '../UserContext';
import AceEditor from 'react-ace';
import 'ace-builds/src-noconflict/mode-javascript';
import 'ace-builds/src-noconflict/theme-github';

const AddAgent = () => {
    const { user, setUser } = useContext(UserContext);
    const navigate = useNavigate();

    const [hover, setHover] = useState({
        name: false,
        description: false,
        readme: false,
        source: false,
        apiKeyRequired: false,
        skeletonCode: false,
        origin: false,
        additionalResources: false,
        tag: false
    });

    const [newAgent, setNewAgent] = useState({
        name: '',
        author: user?.email || '',
        description: '',
        readme: '',
        source: '',
        apiKeyRequired: false,
        skeletonCode: '',
        origin: '',
        additionalResources: '',
        tag: '',
    });

    const tags = [
        "Productivity",
        "Database",
        "Finance",
        "Science",
        "Search",
        "AI",
        "Multimodal"
    ];

    const formStyles = {
        display: 'flex',
        flexDirection: 'column',
        maxWidth: '600px',
        margin: '0 auto',
        padding: '20px',
        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
        borderRadius: '8px',
        backgroundColor: 'white',
        marginTop: '100px',
    };

    const inputStyles = {
        marginBottom: '20px',
        padding: '10px',
        fontSize: '16px',
        borderRadius: '5px',
        border: '1px solid #ddd',
        width: '100%',
    };

    const textareaStyles = {
        marginBottom: '20px',
        padding: '10px',
        fontSize: '16px',
        borderRadius: '5px',
        border: '1px solid #ddd',
        width: '100%',
        minHeight: '100px',
        resize: 'vertical',
    };

    const labelStyles = {
        marginBottom: '5px',
        fontWeight: 'bold',
        position: 'relative'
    };

    const tooltipStyles = {
        position: 'absolute',
        top: '100%',
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: '#f9f9f9',
        padding: '10px',
        borderRadius: '5px',
        boxShadow: '0 2px 5px rgba(0, 0, 0, 0.1)',
        opacity: 1,
        zIndex: 1000,
        display: 'none'
    };

    const buttonStyles = {
        padding: '10px 15px',
        fontSize: '18px',
        borderRadius: '5px',
        border: 'none',
        backgroundColor: '#007bff',
        color: 'white',
        cursor: 'pointer',
        transition: 'background-color 0.3s ease',
        width: 'fit-content',
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setNewAgent(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleEditorChange = (newValue) => {
        setNewAgent(prevState => ({
            ...prevState,
            skeletonCode: newValue
        }));
    };

    const handleHover = (field, isHovering) => {
        setHover(prevState => ({
            ...prevState,
            [field]: isHovering
        }));
    };

    useEffect(() => {
        if (!user) {
            navigate('/login');
        }
    }, [user, navigate]);

    const handleSubmit = (e) => {
        e.preventDefault();
        const email = user.email;

        if (user && user.token) {
            const agentData = { ...newAgent, email };
            axios.post('https://agent-marketplace-2jmb.vercel.app/api/agents', agentData, {
                headers: {
                    'Authorization': `Bearer ${user.token}`
                }
            })
                .then(response => {
                    alert('Agent added successfully');
                    navigate('/');
                })
                .catch(error => {
                    console.error('There was an error adding the agent:', error);
                    alert('Error adding agent');
                });
        } else {
            navigate('/login');
        }
    };

    const backButtonStyle = {
        padding: '10px 20px',
        margin: '0 0 20px',
        cursor: 'pointer',
        fontWeight: 'bold',
        fontSize: '1rem',
        minWidth: '100px',
        minHeight: '40px',
        width: 'fit-content',
    };

    return (
        <>
            <div style={formStyles}>
                <button onClick={() => navigate('/')} style={backButtonStyle}>← Go Back</button>
                <h2 style={{ textAlign: 'center' }}>Add New Agent</h2>
                <form onSubmit={handleSubmit}>
                    <div>
                        <label style={labelStyles}>
                            Name:
                            <span
                                onMouseEnter={() => handleHover('name', true)}
                                onMouseLeave={() => handleHover('name', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.name ? 'block' : 'none' }}>
                                The name of the agent.
                            </div>
                        </label>
                        <input
                            type="text"
                            name="name"
                            value={newAgent.name}
                            onChange={handleInputChange}
                            required
                            style={inputStyles}
                        />
                    </div>
                    <div>
                        <label style={labelStyles}>
                            Description:
                            <span
                                onMouseEnter={() => handleHover('description', true)}
                                onMouseLeave={() => handleHover('description', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.description ? 'block' : 'none' }}>
                                A brief description of what the agent does.
                            </div>
                        </label>
                        <textarea
                            name="description"
                            value={newAgent.description}
                            onChange={handleInputChange}
                            required
                            style={textareaStyles}
                        />
                    </div>
                    <div>
                        <label style={labelStyles}>
                            ReadMe:
                            <span
                                onMouseEnter={() => handleHover('readme', true)}
                                onMouseLeave={() => handleHover('readme', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.readme ? 'block' : 'none' }}>
                                The content of the Readme.MD, including instructions.
                            </div>
                        </label>
                        <textarea
                            name="readme"
                            value={newAgent.readme}
                            onChange={handleInputChange}
                            required
                            style={textareaStyles}
                        />
                    </div>
                    <div>
                        <label style={labelStyles}>
                            Source:
                            <span
                                onMouseEnter={() => handleHover('source', true)}
                                onMouseLeave={() => handleHover('source', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.source ? 'block' : 'none' }}>
                                URL of the source GitHub repository.
                            </div>
                        </label>
                        <input
                            type="text"
                            name="source"
                            value={newAgent.source}
                            onChange={handleInputChange}
                            required
                            style={inputStyles}
                        />
                    </div>
                    <div>
                        <label style={labelStyles}>
                            Skeleton Code:
                            <span
                                onMouseEnter={() => handleHover('skeletonCode', true)}
                                onMouseLeave={() => handleHover('skeletonCode', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.skeletonCode ? 'block' : 'none' }}>
                                Skeleton code for the agent.
                            </div>
                        </label>
                        <AceEditor
                            mode="javascript"
                            theme="github"
                            name="skeletonCode"
                            value={newAgent.skeletonCode}
                            onChange={handleEditorChange}
                            fontSize={16}
                            width="100%"
                            height="200px"
                            style={{ marginBottom: '20px', borderRadius: '5px', border: '1px solid #ddd' }}
                        />
                    </div>
                    <div>
                        <label style={labelStyles}>
                            Origin:
                            <span
                                onMouseEnter={() => handleHover('origin', true)}
                                onMouseLeave={() => handleHover('origin', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.origin ? 'block' : 'none' }}>
                                Origin of the Project (open-source library).
                            </div>
                        </label>
                        <textarea
                            name="origin"
                            value={newAgent.origin}
                            onChange={handleInputChange}
                            required
                            style={textareaStyles}
                        />
                    </div>
                    <div>
                        <label style={labelStyles}>
                            Additional Resources:
                            <span
                                onMouseEnter={() => handleHover('additionalResources', true)}
                                onMouseLeave={() => handleHover('additionalResources', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.additionalResources ? 'block' : 'none' }}>
                                Any additional resources related to the agent.
                            </div>
                        </label>
                        <textarea
                            name="additionalResources"
                            value={newAgent.additionalResources}
                            onChange={handleInputChange}
                            required
                            style={textareaStyles}
                        />
                    </div>
                    <div>
                        <label style={labelStyles}>
                            Tag:
                            <span
                                onMouseEnter={() => handleHover('tag', true)}
                                onMouseLeave={() => handleHover('tag', false)}
                            >?</span>
                            <div style={{ ...tooltipStyles, display: hover.tag ? 'block' : 'none' }}>
                                Select a category tag for the agent.
                            </div>
                        </label>
                        <select
                            name="tag"
                            value={newAgent.tag}
                            onChange={handleInputChange}
                            required
                            style={inputStyles}
                        >
                            <option value="">Select a tag</option>
                            {tags.map(tag => (
                                <option key={tag} value={tag}>{tag}</option>
                            ))}
                        </select>
                    </div>
                    <button type="submit" style={buttonStyles}>
                        Add Agent
                    </button>
                </form>
            </div>
        </>
    );
};

export default AddAgent;
