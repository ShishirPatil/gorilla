import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Form, Button, Container, Row, Col, Card, Collapse } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import CodeEditor from './CodeEditor';
import AgentDropdown from './AgentDropdown';
import { toast } from 'react-toastify';

const apiKeysList = [
  "SERPER_API_KEY",
  "OPENAI_API_KEY",
  "COMPOSIO_API_KEY",
  "ALPHAVANTAGE_API_KEY",
  "BRAVESEARCH_API_KEY",
  "EXA_API_KEY",
  "ANTHROPIC_API_KEY",
  "OPENWEATHERMAP_API_KEY",
  "SERPAPI_API_KEY",
  "ASKNEWS_CLIENT_ID",
  "ASKNEWS_CLIENT_SECRET",
  "TAVILY_API_KEY",
  "EDENAI_API_KEY",
  "E2B_API_KEY",
  "RIZA_API_KEY",
  "GOLDEN_API_KEY",
  "WOLFRAM_APP_ID",
  "WOLFRAM_ALPHA_APPID",
  "YELP_CLIENT_ID",
  "YELP_API_KEY",
  "LANGCHAIN_API_KEY",
  "GOOGLE_CLOUD_PROJECT_ID",
  "GOOGLE_CLOUD_PRIVATE_KEY_ID",
  "GOOGLE_CLOUD_PRIVATE_KEY",
  "GOOGLE_CLOUD_CLIENT_EMAIL",
  "GOOGLE_CLOUD_CLIENT_ID",
  "GOOGLE_CLOUD_AUTH_URI",
  "GOOGLE_CLOUD_TOKEN_URI",
  "GOOGLE_CLOUD_AUTH_PROVIDER_CERT_URL",
  "GOOGLE_CLOUD_CLIENT_CERT_URL",
  "TOGETHER_API_KEY",
  "MISTRAL_API_KEY",
];

const UserProfile = () => {
  const [profile, setProfile] = useState(null);
  const [prompts, setPrompts] = useState([]);
  const [newPrompt, setNewPrompt] = useState('');
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedAgentPrompts, setSelectedAgentPrompts] = useState([]);
  const [initialCode, setInitialCode] = useState('');
  const [editProfile, setEditProfile] = useState({
    name: '',
    email: '',
    bio: '',
    role: '',
    apiKeys: {},
  });
  const [apiKeysExpanded, setApiKeysExpanded] = useState(false); // New state for API keys collapse

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get('https://agent-arena.vercel.app/api/profile', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setProfile(response.data);
        setEditProfile({
          name: response.data.name,
          email: response.data.email,
          bio: response.data.bio,
          role: response.data.role,
          apiKeys: response.data.apiKeys || {}, // Ensure this exists
        });
      } catch (error) {
        console.error('Error fetching profile:', error);
      }
    };

    const fetchAgents = async () => {
      try {
        const response = await axios.get('https://agent-arena.vercel.app/api/agents');
        setAgents(response.data);
      } catch (error) {
        console.error('Error fetching agents:', error);
      }
    };

    const fetchUserPrompts = async () => {
      try {
        const response = await axios.get('https://agent-arena.vercel.app/api/prompts/user', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setPrompts(response.data);
      } catch (error) {
        console.error('Error fetching user prompts:', error);
      }
    };

    fetchProfile();
    fetchAgents();
    fetchUserPrompts();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      const agentPrompts = prompts.filter(prompt => 
        (prompt.leftAgent?._id === selectedAgent._id || 
         prompt.rightAgent?._id === selectedAgent._id || 
         prompt.agent?._id === selectedAgent._id)
      );
      setSelectedAgentPrompts(agentPrompts);
      setInitialCode(selectedAgent.code || '');
    } else {
      setSelectedAgentPrompts(prompts);
    }
  }, [selectedAgent, prompts]);

  const handleSavePrompt = async () => {
    try {
      const response = await axios.post('https://agent-arena.vercel.app/api/prompts/save', { agent: selectedAgent._id, text: newPrompt, executedCode: initialCode }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const newPromptData = response.data;
      setPrompts([...prompts, newPromptData]); // Update prompts with the newly saved prompt
      setNewPrompt(''); // Clear the input field after saving

      // Re-fetch user prompts to ensure the latest data is displayed
      const updatedPromptsResponse = await axios.get('https://agent-arena.vercel.app/api/prompts/user', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const updatedPrompts = updatedPromptsResponse.data;
      setPrompts(updatedPrompts);

      // Update selectedAgentPrompts if the new prompt belongs to the selected agent
      if (selectedAgent) {
        const agentPrompts = updatedPrompts.filter(prompt => 
          (prompt.leftAgent?._id === selectedAgent._id || 
           prompt.rightAgent?._id === selectedAgent._id || 
           prompt.agent?._id === selectedAgent._id)
        );
        setSelectedAgentPrompts(agentPrompts);
      }
    } catch (error) {
      console.error('Error saving prompt:', error);
    }
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setEditProfile(prevState => ({
      ...prevState,
      [name]: value,
    }));
  };

  const handleApiKeyChange = (e) => {
    const { name, value } = e.target;
    setEditProfile(prevState => ({
      ...prevState,
      apiKeys: {
        ...prevState.apiKeys,
        [name]: value,
      },
    }));
  };

  const handleProfileSave = async () => {
    try {
      await axios.put('https://agent-arena.vercel.app/api/profile', editProfile, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      toast.success('Profile updated successfully');
    } catch (error) {
      console.error('Error updating profile:', error);
    }
  };

  const handleAPIKeysSave = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(`https://agent-arena.vercel.app/api/users/${profile._id}/api-keys`, {
        apiKeys: editProfile.apiKeys
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('API Keys updated successfully');
      setProfile(response.data); // Update local profile state with the latest data
    } catch (error) {
      console.error('Error updating API keys:', error);
    }
  };

  const handleLikePrompt = async (promptId) => {
    try {
      await axios.post('https://agent-arena.vercel.app/api/prompts/like', { promptId }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const updatedPrompts = prompts.map(prompt => 
        prompt._id === promptId ? { ...prompt, likes: prompt.likes + 1 } : prompt
      );
      setPrompts(updatedPrompts);
    } catch (error) {
      console.error('Error liking prompt:', error);
    }
  };

  const handleDislikePrompt = async (promptId) => {
    try {
      await axios.post('https://agent-arena.vercel.app/api/prompts/dislike', { promptId }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const updatedPrompts = prompts.map(prompt => 
        prompt._id === promptId ? { ...prompt, dislikes: prompt.dislikes + 1 } : prompt
      );
      setPrompts(updatedPrompts);
    } catch (error) {
      console.error('Error disliking prompt:', error);
    }
  };

  return (
    <Container className="mt-4">
      <Card>
        <Card.Body>
          <h1>{profile ? `${profile.name}'s Profile` : "Profile"}</h1>
          <Form>
            <Row className="mb-3">
              <Col>
                <Form.Group controlId="formName">
                  <Form.Label>Name</Form.Label>
                  <Form.Control type="text" name="name" value={editProfile.name} onChange={handleProfileChange} />
                </Form.Group>
              </Col>
              <Col>
                <Form.Group controlId="formEmail">
                  <Form.Label>Email</Form.Label>
                  <Form.Control type="email" name="email" value={editProfile.email} onChange={handleProfileChange} disabled />
                </Form.Group>
              </Col>
            </Row>
            <Row className="mb-3">
              <Col>
                <Form.Group controlId="formBio">
                  <Form.Label>Bio</Form.Label>
                  <Form.Control type="text" name="bio" value={editProfile.bio} onChange={handleProfileChange} />
                </Form.Group>
              </Col>
              <Col>
                <Form.Group controlId="formRole">
                  <Form.Label>Role</Form.Label>
                  <Form.Control type="text" name="role" value={editProfile.role} onChange={handleProfileChange} />
                </Form.Group>
              </Col>
            </Row>
            <Button variant="primary" onClick={handleProfileSave} className="mb-3">Save Profile</Button>
            <hr />
            <h2>API Keys</h2>
            <p>
              API keys are required for specific agents to function properly. You can add your own keys for better performance 
              and to avoid rate limits. Please ensure you enter the correct key for each API.
            </p>
            <Button
              variant="secondary"
              onClick={() => setApiKeysExpanded(!apiKeysExpanded)}
              aria-controls="api-keys-collapse"
              aria-expanded={apiKeysExpanded}
            >
              {apiKeysExpanded ? 'Hide API Keys' : 'Manage API Keys'}
            </Button>
            <Collapse in={apiKeysExpanded}>
              <div id="api-keys-collapse">
                {apiKeysList.map(key => (
                  <Row className="mb-3" key={key}>
                    <Col>
                      <Form.Group controlId={`form${key}`}>
                        <Form.Label>{key.replace(/_/g, ' ')}</Form.Label>
                        <Form.Control 
                          type="text" 
                          name={key} 
                          value={editProfile.apiKeys[key] || ''} 
                          onChange={handleApiKeyChange} 
                          placeholder={`Enter your ${key.replace(/_/g, ' ')} here`} 
                        />
                      </Form.Group>
                    </Col>
                  </Row>
                ))}
                <Button variant="primary" onClick={handleAPIKeysSave} className="mb-3">Save API Keys</Button>
              </div>
            </Collapse>
          </Form>
          <hr />
          <h2>Saved Prompts</h2>
          <AgentDropdown agents={agents} selectedAgent={selectedAgent} onSelect={setSelectedAgent} />
          <Form.Group controlId="formNewPrompt" className="mb-3">
            <Form.Label>New Prompt</Form.Label>
            <Form.Control
              type="text"
              placeholder="New Prompt"
              value={newPrompt}
              onChange={(e) => setNewPrompt(e.target.value)}
            />
          </Form.Group>
          <Button variant="success" onClick={handleSavePrompt} className="mb-3">Save Prompt</Button>
          {selectedAgent && (
            <>
              {selectedAgentPrompts.length > 0 ? (
                selectedAgentPrompts.map(prompt => (
                  <Link to={`/prompts/${prompt._id}`} key={prompt._id} style={{ textDecoration: 'none' }}>
                    <Card className="mb-4" style={{ backgroundColor: '#f8f9fa', borderColor: '#17a2b8' }}>
                      <Card.Body>
                        <p>{prompt.text}</p>
                        <Button variant="outline-success" onClick={(e) => { e.preventDefault(); handleLikePrompt(prompt._id); }}>Like ({prompt.likes})</Button>
                        <Button variant="outline-danger" onClick={(e) => { e.preventDefault(); handleDislikePrompt(prompt._id); }} className="ml-2">Dislike ({prompt.dislikes})</Button>
                      </Card.Body>
                    </Card>
                  </Link>
                ))
              ) : (
                <p>No saved prompts for this agent.</p>
              )}
              <CodeEditor agentId={selectedAgent._id} initialCode={initialCode} onExecute={() => {}} />
            </>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default UserProfile;
