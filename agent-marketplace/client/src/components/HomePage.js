import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import Card from './Card';
import '../App.css';
import { useLocation, useNavigate } from 'react-router-dom'; // Import useNavigate
import UserContext from '../UserContext';
import './Nav.css'; // Import the CSS file
import ProgressBar from './ProgressBar'; // Import the ProgressBar component

const HomePage = () => {
  const [agents, setAgents] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const location = useLocation(); // Get access to the location object
  const urlNavigate = useNavigate(); // Renamed to avoid conflict
  const [showMyAgents, setShowMyAgents] = useState(false); // [1
  const { user, setUser } = useContext(UserContext);
  const [agentOrigin, setAgentOrigin] = useState('');
  const filters = ["AI", "Data", "Integration", "Communication", "Database", "Finance", "langchain", "llama-index", "openai", "crewai"];
  const [selectedFilters, setSelectedFilters] = useState([]);
  const [fetchError, setFetchError] = useState(false); // State to track fetch errors

  useEffect(() => {
    const fetchAgents = async () => {
      setFetchError(false); // Reset error state before fetching

      try {
        const baseUrl = 'https://agent-marketplace-2jmb.vercel.app'; // Define the base URL
        let url = showMyAgents ? `${baseUrl}/api/my-agents` : `${baseUrl}/api/agents`;
        console.log(url);

        // Include the email as a query parameter if showing the user's agents
        if (showMyAgents && user?.email) {
          // Append the email query parameter
          url += `?email=${encodeURIComponent(user.email)}`;
        }

        const response = await axios.get(url);
        setAgents(response.data);
        if (response.data.length === 0 && showMyAgents) {
          setFetchError(true); // Set error if no agents found and showMyAgents is true
        }
      } catch (error) {
        console.error('There was an error fetching the agents:', error);
        setFetchError(true);
      }
    };

    fetchAgents();
  }, [showMyAgents, user?.token, user?.email]); // Dependency array to trigger useEffect

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const searchQuery = searchParams.get('search');
    if (searchQuery !== null) {
      setSearchTerm(searchQuery);
    }
  }, [location.search]);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    if (searchTerm) {
      searchParams.set('search', searchTerm);
    } else {
      searchParams.delete('search');
    }
    urlNavigate(`/?${searchParams.toString()}`, { replace: true });
  }, [searchTerm, urlNavigate, location.search]);

  // console.log(agents[0])
  const filteredAgents = agents.filter(agent =>
    (agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
     agent.description.toLowerCase().includes(searchTerm.toLowerCase())) &&
    (selectedFilters.length === 0 || selectedFilters.some(filter => filter === agent.tag || filter === agent.origin || (filter === "llama-index" && agent.origin === "llama")))
  );

  console.log(filteredAgents)
  console.log(agentOrigin)

  const toggleFilter = (filter) => {
    setSelectedFilters(prevFilters => {
      if (prevFilters.includes(filter)) {
        return prevFilters.filter(f => f !== filter);
      } else {
        return [...prevFilters, filter];
      }
    });
  };

  const toggleShowMyAgents = () => {
    setShowMyAgents(!showMyAgents);
  };

  const filterButtonStyles = {
    padding: '10px 20px',
    border: '1px solid #007bff',
    borderRadius: '20px',
    backgroundColor: 'transparent',
    color: '#007bff',
    cursor: 'pointer',
    flex: '0 1 auto', // Flex property to prevent the button from growing too large
    maxWidth: '200px', // Ensure buttons do not grow too wide
    '@media (max-width: 768px)': {
      padding: '8px 10px', // Smaller padding on small screens
      fontSize: '14px', // Smaller font size on small screens
    },
  };

  const clearFilterButtonStyles = {
    ...filterButtonStyles,
    border: '1px solid #ccc',
    color: '#333',
  };

  const filterContainerStyles = {
    display: 'flex',
    flexWrap: 'wrap', // Allow buttons to wrap to the next line
    gap: '10px',
    marginBottom: '20px',
    padding: '10px 20px',

    '@media (max-width: 768px)': {
      flexDirection: 'column',
      justifyContent: 'center', // Stack buttons vertically on very small screens
      alignItems: 'center',
    }
  };

  const taglineStyles = {
    textAlign: 'center',
    fontSize: '1rem', // Slightly smaller font size
    color: '#666', // Slightly greyer color
    marginBottom: '40px',
    maxWidth: '800px',
    lineHeight: '1.5',
    margin: '20px auto', // Add margin to move it below the search bar
  };

  const navigate = (path) => {
    window.location.href = path; // Navigate to specified path
  };

  const navigateToAddAgent = () => {
    navigate('/add-agent');
  };

  const handleLogout = () => {
    setUser(null); // Clears user from context
    localStorage.removeItem('user-info'); // Clears user info from localStorage if used for persisting login state
    navigate('/login'); // Redirects to the login page
  };

  const renderAgents = () => {
    if (fetchError) {
      return <p style={{ textAlign: 'center' }}>You have no agents.</p>;
    } else if (filteredAgents.length > 0) {
      return filteredAgents.map(agent => <Card key={agent._id} agent={agent} />);
    } else {
      return <p style={{ textAlign: 'center' }}>No agents found.</p>;
    }
  };

  return (
    <>
      <div style={{ maxWidth: '1200px', margin: '60px auto', padding: '20px' }}>
        <div className={`navButtonsContainer ${window.innerWidth <= 768 ? 'mobile' : ''}`}>
          {user ? (
            <>
              <button onClick={handleLogout} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Logout</button>
              <button onClick={toggleShowMyAgents} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>
                {showMyAgents ? 'Show All Agents' : 'Show My Agents'}
              </button>
            </>
          ) : (
            <button onClick={() => urlNavigate('/login')} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Login</button>
          )}
          <button onClick={navigateToAddAgent} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Add New Agent</button>
          <button onClick={() => urlNavigate('/faqs')} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>FAQs</button>
          <button onClick={() => window.location.href = 'https://gorilla.cs.berkeley.edu/blogs/11_agent_marketplace.html'} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Blog</button> {/* New Blog button */}
        </div>

        <h1 style={{ textAlign: 'center', fontSize: '2.5rem', margin: '20px 0 10px 0', color: '#007bff', fontFamily: 'Arial' }}>Agents and Assistants Marketplace</h1>
        <p style={{
          textAlign: 'center',
          fontSize: '1.2rem',
          color: '#333',
          marginBottom: '10px',
          maxWidth: '800px',
          lineHeight: '1.8',
          margin: '0 auto 20px'
        }}>
          Opensource Search Engine for LLM Agents
        </p>
        <p style={taglineStyles}>
          Featuring over 150 certified agents from Langchain, Llamaindex, OpenAI, and CrewAI, all accessible through a unified interface with user reviews
        </p>
        
        {/* ProgressBar Component */}
        <ProgressBar runningAgents={157} totalAgents={agents.length} />

        <input
          type="text"
          placeholder="Search for agents..."
          style={{
            width: 'calc(100% - 30px)',
            padding: '15px',
            marginBottom: '40px',
            fontSize: '18px',
            border: '2px solid #007bff',
            borderRadius: '25px',
            outline: 'none',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease'
          }}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <div style={filterContainerStyles}>
          {filters.map(filter => (
            <button
              key={filter}
              onClick={() => toggleFilter(filter)}
              style={{
                ...filterButtonStyles,
                padding: '10px 20px',
                border: '1px solid #007bff',
                borderRadius: '20px',
                backgroundColor: selectedFilters.includes(filter) ? '#007bff' : 'transparent',
                color: selectedFilters.includes(filter) ? 'white' : '#007bff',
                cursor: 'pointer'
              }}
            >
              {filter}
            </button>
          ))}
          <button
            onClick={() => setSelectedFilters([])}
            style={clearFilterButtonStyles}
          >
            Clear Filters
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '50px', justifyContent: 'center' }}>
          {renderAgents()}
        </div>
      </div>
    </>
  );
};

export default HomePage;
