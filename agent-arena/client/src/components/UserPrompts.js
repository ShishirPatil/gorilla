import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';
import { Card, Button, Container, Row, Col, Form } from 'react-bootstrap';
import CodeEditor from './CodeEditor';
import AgentDropdown from './AgentDropdown';
import { toast } from 'react-toastify';
import Select from 'react-select';

const UserPrompts = () => {
  const { userId } = useParams();
  const [prompts, setPrompts] = useState([]);
  const [filteredPrompts, setFilteredPrompts] = useState([]);
  const [user, setUser] = useState({});
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedAgentPrompts, setSelectedAgentPrompts] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [initialCode, setInitialCode] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState('');

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          const response = await axios.get(`https://agent-arena.vercel.app/api/profile`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setCurrentUserId(response.data._id);
        }
      } catch (error) {
        console.error('Error fetching user:', error);
      }
    };

    const fetchPrompts = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const response = await axios.get(`https://agent-arena.vercel.app/api/prompts/user/${userId}`, { headers });
        setPrompts(response.data);
        setFilteredPrompts(response.data);
      } catch (error) {
        console.error('Error fetching prompts:', error);
      }
    };

    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const response = await axios.get(`https://agent-arena.vercel.app/api/users/${userId}`, { headers });
        setUser(response.data);
      } catch (error) {
        console.error('Error fetching user data:', error);
      }
    };

    const fetchAgents = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const response = await axios.get(`https://agent-arena.vercel.app/api/agents`, { headers });
        setAgents(response.data);
      } catch (error) {
        console.error('Error fetching agents:', error);
      }
    };

    fetchUser();
    fetchPrompts();
    fetchUserData();
    fetchAgents();
  }, [userId]);

  useEffect(() => {
    if (selectedAgent) {
      const agentPrompts = prompts.filter(prompt => 
        (prompt.leftAgent && prompt.leftAgent._id === selectedAgent._id) ||
        (prompt.rightAgent && prompt.rightAgent._id === selectedAgent._id) ||
        (prompt.agent && prompt.agent._id === selectedAgent._id)
      );
      setSelectedAgentPrompts(agentPrompts);
      setInitialCode(selectedAgent.code || '');
    } else {
      setSelectedAgentPrompts(filteredPrompts);
    }
  }, [selectedAgent, filteredPrompts]);

  const handleLike = async (promptId) => {
    if (!currentUserId) {
      toast.error('You need to be logged in to like prompts');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post('https://agent-arena.vercel.app/api/prompts/like', { promptId }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const response = await axios.get(`https://agent-arena.vercel.app/api/prompts/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPrompts(response.data);
      setFilteredPrompts(response.data);
    } catch (error) {
      console.error('Error liking prompt:', error);
    }
  };

  const handleDislike = async (promptId) => {
    if (!currentUserId) {
      alert("You need to be logged in to dislike prompts.");
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post('https://agent-arena.vercel.app/api/prompts/dislike', { promptId }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const response = await axios.get(`https://agent-arena.vercel.app/api/prompts/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPrompts(response.data);
      setFilteredPrompts(response.data);
    } catch (error) {
      console.error('Error disliking prompt:', error);
    }
  };

  const handleSearch = (e) => {
    setSearchQuery(e.target.value);
    const query = e.target.value.toLowerCase();
    setFilteredPrompts(prompts.filter(prompt => 
      prompt.text.toLowerCase().includes(query)
    ));
  };

  const handleSortChange = (selectedOption) => {
    setSortOption(selectedOption.value);
    let sortedPrompts;
    if (selectedOption.value === 'likes') {
      sortedPrompts = [...filteredPrompts].sort((a, b) => b.likes - a.likes);
    } else if (selectedOption.value === 'dislikes') {
      sortedPrompts = [...filteredPrompts].sort((a, b) => b.dislikes - a.dislikes);
    }
    setFilteredPrompts(sortedPrompts);
  };

  const sortOptions = [
    { value: 'likes', label: 'Likes' },
    { value: 'dislikes', label: 'Dislikes' },
  ];

  const customStyles = {
    control: (base) => ({
      ...base,
      minHeight: 40,
      fontSize: 14,
      width: '100%',
    }),
    menu: (base) => ({
      ...base,
      fontSize: 14,
    }),
    singleValue: (base) => ({
      ...base,
      color: '#4b0082',
    }),
    option: (base, { isFocused }) => ({
      ...base,
      color: '#4b0082',
      backgroundColor: isFocused ? '#d3d3d3' : 'white',
    }),
  };

  return (
    <Container className="mt-4">
      <h1>{user.name}'s Prompts</h1>
      <p>{user.bio}</p>
      <p>Role: {user.role}</p>
      <Row className="mb-4">
        <Col md={6}>
          <Form.Control
            type="text"
            placeholder="Search prompts..."
            value={searchQuery}
            onChange={handleSearch}
            className="mb-4"
          />
        </Col>
        <Col md={6}>
          <Select
            options={sortOptions}
            onChange={handleSortChange}
            placeholder="Sort by..."
            styles={customStyles}
          />
        </Col>
      </Row>
      <AgentDropdown agents={agents} selectedAgent={selectedAgent} onSelect={setSelectedAgent} />
      {selectedAgentPrompts.map(prompt => (
        <Link to={`/prompts/${prompt._id}`} key={prompt._id} style={{ textDecoration: 'none' }}>
          <Card className="mb-4" style={{ backgroundColor: '#1c1c1e', borderColor: '#17a2b8' }}>
            <Card.Body>
              <p>{prompt.text}</p>
              <Button variant="outline-success" onClick={(e) => { e.preventDefault(); handleLike(prompt._id); }} className="mr-2">
                Like ({prompt.likes})
              </Button>
              <Button variant="outline-danger" onClick={(e) => { e.preventDefault(); handleDislike(prompt._id); }}>
                Dislike ({prompt.dislikes})
              </Button>
            </Card.Body>
          </Card>
        </Link>
      ))}
      {selectedAgent && (
        <CodeEditor agentId={selectedAgent._id} initialCode={initialCode} onExecute={() => {}} />
      )}
    </Container>
  );
};

export default UserPrompts;
