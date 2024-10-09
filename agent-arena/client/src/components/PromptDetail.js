import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Container, Row, Col, Form, Alert, Button } from 'react-bootstrap';
import StaticCodeEditor from './StaticCodeEditor';
import CodeEditor from './CodeEditor';
import AgentDropdown from './AgentDropdown';
import { toast } from 'react-toastify';

const PromptDetail = () => {
  const { promptId } = useParams();
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState(null);
  const [leftAgent, setLeftAgent] = useState(null);
  const [rightAgent, setRightAgent] = useState(null);
  const [agent, setAgent] = useState(null);
  const [agents, setAgents] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [leftExecutedCode, setLeftExecutedCode] = useState('');
  const [rightExecutedCode, setRightExecutedCode] = useState('');

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

    const fetchAgents = async () => {
      try {
        const response = await axios.get('https://agent-arena.vercel.app/api/agents');
        setAgents(response.data);
      } catch (error) {
        console.error('Error fetching agents:', error);
      }
    };

    const fetchPrompt = async () => {
      try {
        const response = await axios.get(`https://agent-arena.vercel.app/api/prompts/${promptId}`);
        setPrompt(response.data);

        if (response.data.leftAgent) {
          const leftAgentResponse = await axios.get(`https://agent-arena.vercel.app/api/agents/${response.data.leftAgent._id}`);
          setLeftAgent(leftAgentResponse.data);
        }
        if (response.data.rightAgent) {
          const rightAgentResponse = await axios.get(`https://agent-arena.vercel.app/api/agents/${response.data.rightAgent._id}`);
          setRightAgent(rightAgentResponse.data);
        }
        if (response.data.agent) {
          const agentResponse = await axios.get(`https://agent-arena.vercel.app/api/agents/${response.data.agent._id}`);
          setAgent(agentResponse.data);
        }
      } catch (error) {
        console.error('Error fetching prompt:', error);
      }
    };

    fetchUser();
    fetchAgents();
    fetchPrompt();
  }, [promptId]);

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
      const response = await axios.get(`https://agent-arena.vercel.app/api/prompts/${promptId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPrompt(response.data);
    } catch (error) {
      console.error('Error liking prompt:', error);
    }
  };

  const handleDislike = async (promptId) => {
    if (!currentUserId) {
      toast.error('You need to be logged in to dislike prompts');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post('https://agent-arena.vercel.app/api/prompts/dislike', { promptId }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const response = await axios.get(`https://agent-arena.vercel.app/api/prompts/${promptId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPrompt(response.data);
    } catch (error) {
      console.error('Error disliking prompt:', error);
    }
  };

  const handleShare = async () => {
    const shareURL = window.location.href;
    navigator.clipboard.writeText(shareURL);
    toast.success('Shareable link copied to clipboard');
  };

  if (!prompt) {
    return <div>Loading...</div>;
  }

  const processedCode = agent ? agent.code.replace('Enter Goal/Prompt Here', prompt.text) : '';

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <Button variant="secondary" onClick={() => navigate(-1)} className="mb-2">
          Go Back
        </Button>
        <Button variant="outline-primary" onClick={handleShare} className="mb-2">
          Share Prompt
        </Button>
      </div>
      <h1 className="text-center mb-4">Prompt Detail</h1>
      <Form.Control
        type="text"
        value={prompt.text}
        readOnly
        className="mb-4 text-center"
        style={{ width: '100%' }}
      />
      <Row className="justify-content-center mb-3">
        <Col md={5} className="text-center">
          <Button variant="outline-success" onClick={() => handleLike(prompt._id)} className="mr-2">
            Like ({prompt.likes})
          </Button>
          <Button variant="outline-danger" onClick={() => handleDislike(prompt._id)}>
            Dislike ({prompt.dislikes})
          </Button>
        </Col>
      </Row>
      <Row className="justify-content-center">
        {leftAgent && rightAgent ? (
          <>
            <Col md={5} className="mb-4">
              <h2 className="text-center">Agent 1</h2>
              <AgentDropdown agents={agents} selectedAgent={leftAgent} onSelect={setLeftAgent} disabled />
              <StaticCodeEditor
                executedCode={prompt.text ? leftAgent.code.replace('Enter Goal/Prompt Here', prompt.text) : leftAgent.code}
                output={prompt.leftOutput}
              />
            </Col>
            <Col md={5} className="mb-4">
              <h2 className="text-center">Agent 2</h2>
              <AgentDropdown agents={agents} selectedAgent={rightAgent} onSelect={setRightAgent} disabled />
              <StaticCodeEditor
                executedCode={prompt.text ? rightAgent.code.replace('Enter Goal/Prompt Here', prompt.text) : rightAgent.code}
                output={prompt.rightOutput}
              />
            </Col>
          </>
        ) : (
          <Col md={6} className="mb-4">
            <h2 className="text-center">Agent</h2>
            <AgentDropdown agents={agents} selectedAgent={agent} onSelect={setAgent} disabled />
            <CodeEditor
              agentId={agent ? agent._id : null}
              initialCode={processedCode}
              output={prompt.output || prompt.leftOutput || prompt.rightOutput}
            />
          </Col>
        )}
      </Row>
      {prompt.votedResult && (
        <Row className="mt-4">
          <Col className="text-center">
            <Alert variant="success" className="p-3">
              <h5>Rating Result: {prompt.votedResult}</h5>
            </Alert>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default PromptDetail;