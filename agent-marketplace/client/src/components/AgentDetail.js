import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { useParams, useNavigate } from 'react-router-dom';
import ReviewForm from './ReviewForm';
import Reviews from './Reviews';
import '../App.css';
import UserContext from '../UserContext';

const AgentDetail = () => {
  const [agent, setAgent] = useState(null);
  const { id: agentId } = useParams();
  const [searchTerm, setSearchTerm] = useState("");
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const [markdown, setMarkdown] = useState('');
  const isUserOwner = user && user.agents && user.agents.includes(agentId);

  const deleteAgent = () => {
    if (!isUserOwner) {
      alert('You do not have permission to delete this agent.');
      return;
    }

    axios.delete(`https://agent-marketplace-2jmb.vercel.app/api/agents/${agentId}`, {
      headers: { Authorization: `Bearer ${user.token}` }
    })
    .then(() => {
      alert('Agent deleted successfully.');
      navigate('/'); 
    })
    .catch(error => {
      console.error('Failed to delete agent:', error);
      alert('Failed to delete agent.');
    });
  };

  useEffect(() => {
    if (!agentId) {
      console.error('Agent ID is not provided');
      return;
    }

    axios.get(`https://agent-marketplace-2jmb.vercel.app/api/agents/${agentId}`)
      .then(response => {
        setAgent(response.data);
        setMarkdown(response.data.skeletonCode || response.data.readme);
      })
      .catch(error => {
        console.error('There was an error fetching the agent details:', error);
      });
  }, [agentId]);

  if (!agent) {
    return <div>Loading agent details...</div>;
  }

  const downloadMarkdown = () => {
    const element = document.createElement("a");
    const file = new Blob([markdown], {type: 'text/markdown;charset=utf-8'});
    element.href = URL.createObjectURL(file);
    element.download = "agent.md";
    document.body.appendChild(element);
    element.click();
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    navigate(`/?search=${searchTerm}`);
  };

  const renderStars = (rating) => {
    let stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} style={{ color: i <= rating ? '#FFD700' : '#e0e0e0' }}>★</span>
      );
    }
    return <div style={{ fontSize: '16px', marginRight: '10px' }}>{stars}</div>;
  };

  const containerStyle = {
    padding: '20px',
    maxWidth: '800px',
    margin: '20px auto',
    boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
    borderRadius: '8px',
    overflowWrap: 'break-word',
    wordWrap: 'break-word',
    whiteSpace: 'pre-wrap',
  };

  const backButtonStyle = {
    padding: '10px 20px',
    margin: '20px 10px 10px',
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '1rem',
    minWidth: '100px',
    minHeight: '40px',
  };

  const markdownStyle = {
    backgroundColor: '#f6f8fa',
    border: '1px solid #eee',
    padding: '10px',
    borderRadius: '5px',
    marginTop: '20px',
    overflowWrap: 'break-word',
    wordWrap: 'break-word',
    whiteSpace: 'pre-wrap',
    maxHeight: '500px',
    overflowY: 'auto',
  };

  const topRightButtonStyle = {
    padding: '10px 20px',
    cursor: 'pointer',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    fontSize: '1rem',
    marginLeft: '0',
    '@media (max-width: 768px)': {
      marginLeft: '0',
    },
  };

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  };

  const standardizedImage = {
    width: '20px',
    height: '20px',
    marginLeft: '10px',
  };

  const ratingStyle = {
    display: 'flex',
    alignItems: 'center',
    marginTop: '10px',
    fontSize: '1rem',
    color: '#333',
  };

  const reviewCountStyle = {
    display: 'flex',
    alignItems: 'center',
    marginLeft: '10px',
  };

  const reviewIconStyle = {
    width: '16px',
    height: '16px',
    marginRight: '5px',
  };

  let imagePath = `/${agent?.origin}.png`;
  if (agent?.origin === 'llama') {
    imagePath = "/llama-index.png";
  }

  return (
    <>
      <div style={containerStyle}>
        <div className="mobile-buttons-container">
          <button onClick={() => navigate(-1)} style={backButtonStyle}>← Go Back</button>
          <button onClick={() => navigate('/faqs')} style={{ ...backButtonStyle, marginLeft: '10px', backgroundColor: '#007bff', color: 'white' }}>
            FAQs
          </button>
        </div>
        <h1 style={{ textAlign: 'center', fontSize: '2.5rem', margin: '30px 0px 10px 0', padding: '30px', color: '#007bff' }}>Agents and Assistants Marketplace</h1>
        <form onSubmit={handleSearchSubmit} style={{ textAlign: 'center', marginBottom: '20px' }}>
          <input
            type="text"
            placeholder="Search for agents..."
            className="searchBox"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" className="searchButton" style={{marginTop:"20px"}}>Search</button>
        </form>
        <div style={{ textAlign: 'center', margin: '20px 0' }}>
          <h1>LLM Agent</h1>
        </div>
        <div style={headerStyle}>
          <h1>{agent?.name}</h1>
          <button style={topRightButtonStyle} onClick={() => window.open(agent?.source, '_blank')}>
            Check it out at {agent?.origin}<img src={imagePath} alt={agent?.origin} style={{ width: '25px', height: '25px', marginLeft: '5px' }} />
          </button>
        </div>
        <p>{agent?.description}</p>
        <div style={ratingStyle}>
          {renderStars(agent.averageRating)}
          <span>{agent.averageRating.toFixed(1)}</span>
          <div style={reviewCountStyle}>
            <img src="/user.png" alt="Reviews" style={reviewIconStyle} />
            <span>{agent.numberOfReviews}</span>
          </div>
        </div>
        {agent.readme && (
          <div style={{
            ...markdownStyle,
            overflowWrap: 'break-word',
            fontSize: '0.7rem',
            fontWeight: 'normal',
          }}>
            <ReactMarkdown>{agent.readme.replace(/\\n/g, '\n')}</ReactMarkdown>
          </div>
        )}
        {agent?.apiKeyRequired && (
          <>
            <p>This agent requires an API key. Input your key in the markdown below and download:</p>
          </>
        )}
        <textarea
          rows="5"
          cols="50"
          style={{ width: '100%', padding: '10px', margin: '10px 0', borderRadius: '5px', border: '1px solid #ddd' }}
          value={markdown}
          onChange={(e) => setMarkdown(e.target.value)}
        />
        <button onClick={downloadMarkdown} style={{ ...backButtonStyle, backgroundColor: '#4CAF50', color: 'white', border: 'none' }}>Download Markdown with API Key</button>
        <a href={agent?.source} target="_blank" rel="noopener noreferrer" style={{ display: 'block', marginTop: '20px', textDecoration: 'none', color: '#007bff' }}>Visit Source→</a>
        {agent.additionalResources && (
          <div style={{ marginTop: '20px' }}>
            <h2>Additional Resources</h2>
            <ReactMarkdown>{agent.additionalResources}</ReactMarkdown>
          </div>
        )}
        <div style={{ marginTop: '40px' }}>
          <h2>Reviews</h2>
          <Reviews agentId={agentId} />
          <h3 style={{ marginTop: '20px' }}>Leave a Review</h3>
          <ReviewForm agentId={agentId} user={user} />
          {isUserOwner && (
            <button onClick={deleteAgent} style={{
              padding: '10px 20px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              marginTop: '20px'
            }}>
              Delete Agent
            </button>
          )}
        </div>
      </div>
    </>
  );
};

export default AgentDetail;
