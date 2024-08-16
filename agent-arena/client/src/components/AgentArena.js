import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Container, Row, Col, Button, Form } from 'react-bootstrap';
import { toast } from 'react-toastify';
import AgentDropdown from './AgentDropdown';
import CodeEditor from './CodeEditor';
import useTypingEffect from './useTypingEffect';
import { ThemeContext } from '../App';

const AgentArena = () => {
  const [leftAgent, setLeftAgent] = useState(null);
  const [rightAgent, setRightAgent] = useState(null);
  const { theme } = useContext(ThemeContext);

  const [goal, setGoal] = useState('');
  const [agents, setAgents] = useState([]);
  const [leftExecutedCode, setLeftExecutedCode] = useState('');
  const [rightExecutedCode, setRightExecutedCode] = useState('');
  const [leftOutput, setLeftOutput] = useState('');
  const [rightOutput, setRightOutput] = useState('');
  const [leftCompleted, setLeftCompleted] = useState(false);
  const [rightCompleted, setRightCompleted] = useState(false);
  const [ratingEnabled, setRatingEnabled] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [votedResult, setVotedResult] = useState('');
  const [shareURL, setShareURL] = useState('');
  const [promptId, setPromptId] = useState(null);
  const [leftFile, setLeftFile] = useState(null);
  const [rightFile, setRightFile] = useState(null);
  const [isExample3, setIsExample3] = useState(false);

  const examplePrompts = [
    "Search the web",
    "Look up stocks",
    "Read MongoDB database and generate plots",
    "Understand company expense reports"
  ];

  const displayedPrompt = useTypingEffect(examplePrompts);

  useEffect(() => {
    axios.get('https://agent-arena.vercel.app/api/agents')
      .then(response => setAgents(response.data))
      .catch(error => console.error(error));

    const token = localStorage.getItem('token');
    if (token) {
      axios.get('https://agent-arena.vercel.app/api/profile', {
        headers: { Authorization: `Bearer ${token}` }
      }).then(response => {
        setIsLoggedIn(true);
      }).catch(error => {
        console.error(error);
      });
    }
  }, []);

  useEffect(() => {
    if (leftCompleted && rightCompleted) {
      setRatingEnabled(true);
    }
  }, [leftCompleted, rightCompleted]);

  const handleLeftSelect = (agent) => {
    setLeftAgent(agent);
    setLeftExecutedCode(goal ? agent.code.replace('Enter Goal/Prompt Here', goal) : agent.code);
    resetVotingState();
  };

  const handleRightSelect = (agent) => {
    setRightAgent(agent);
    setRightExecutedCode(goal ? agent.code.replace('Enter Goal/Prompt Here', goal) : agent.code);
    resetVotingState();
  };

  const resetVotingState = () => {
    setLeftCompleted(false);
    setRightCompleted(false);
    setRatingEnabled(false);
    setHasVoted(false);
    setLeftOutput('');
    setRightOutput('');
    setVotedResult('');
    setShareURL('');
    setPromptId(null);
    setLeftFile(null);
    setRightFile(null);
    setIsExample3(false);
  };

  const handleRating = (rating) => {
    setVotedResult(rating);
    axios.post('https://agent-arena.vercel.app/api/ratings', {
      leftAgent: leftAgent._id,
      rightAgent: rightAgent._id,
      rating,
      executedCode: leftExecutedCode + '\n' + rightExecutedCode,
      leftOutput,
      rightOutput,
      savePrompt: isLoggedIn
    }).then(response => {
      toast.success(response.data.message);
      setHasVoted(true);
      setRatingEnabled(false);
      setPromptId(response.data.promptId);
    }).catch(error => {
      toast.error('Error saving rating');
    });
  };

  const handleSavePrompt = async () => {
    if (!isLoggedIn) {
      toast.error('You need to be logged in to save prompts');
      return;
    }

    try {
      const response = await axios.post('https://agent-arena.vercel.app/api/prompts/save', {
        text: goal,
        leftAgent: leftAgent._id,
        rightAgent: rightAgent._id,
        leftExecutedCode,
        rightExecutedCode,
        votedResult,
        leftOutput,
        rightOutput
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      toast.success('Prompt saved successfully');
      setPromptId(response.data._id);
      setShareURL(`https://www.agent-arena.com/prompts/${response.data._id}`);
    } catch (error) {
      console.error('Error saving prompt:', error);
      toast.error('Error saving prompt');
    }
  };

  const handleSearch = async () => {
    if (!agents.length) {
      toast.error('No agents available for selection');
      return;
    }

    try {
      const agentNames = agents.map(agent => agent.name);
      const response = await axios.post('https://agent-arena.vercel.app/api/goals/interpret-goal', { goal, agentNames });
      const { agent1, agent2 } = response.data;
      setLeftAgent(agent1);
      setRightAgent(agent2);
      setLeftExecutedCode(goal ? agent1.code.replace('Enter Goal/Prompt Here', goal) : agent1.code);
      setRightExecutedCode(goal ? agent2.code.replace('Enter Goal/Prompt Here', goal) : agent2.code);
      resetVotingState();
    } catch (error) {
      toast.error('Error interpreting goal');
    }
  };

  const handleShareSession = async () => {
    try {
      const response = await axios.post('https://agent-arena.vercel.app/api/share', {
        promptId: promptId
      });
      navigator.clipboard.writeText(response.data.url);
      toast.success('Session link copied to clipboard');
    } catch (error) {
      toast.error('Error sharing session');
    }
  };

  const setExample = async (exampleNumber) => {
    resetVotingState(); // Reset the voting state before setting the goal and agents
    let newGoal = '';

    switch (exampleNumber) {
      case 1:
        newGoal = 'What is new in California today';
        break;
      case 2:
        newGoal = 'what was AAPL stock yesterday';
        break;
      case 3:
        newGoal = 'plot salary and first name given an sql database';
        setIsExample3(true);
        try {
          const response = await axios.get('https://agent-arena-wuwl.onrender.com/api/db/company', { responseType: 'blob' });
          const file = new File([response.data], 'company.db', { type: 'application/x-sqlite3' });
          setLeftFile(file);
          setRightFile(file);
        } catch (error) {
          toast.error('Error fetching company.db');
        }
        break;
      default:
        break;
    }

    setGoal(newGoal);
    await loadExampleAgents(newGoal);
  };

  const loadExampleAgents = async (goal) => {
    let leftAgentName = '';
    let rightAgentName = '';

    switch (goal) {
      case 'What is new in California today':
        leftAgentName = 'langchain google-serper search agent (gpt-4o-2024-08-06)';
        rightAgentName = 'langchain brave-search agent (gpt-4o-2024-08-06)';
        break;
      case 'what was AAPL stock yesterday':
        leftAgentName = 'langchain alpha-vantage stock agent (gpt-4-turbo-2024-04-09)';
        rightAgentName = 'langchain alpha-vantage stock agent (claude-3-opus-20240229)';
        break;
      case 'plot salary and first name given an sql database':
        leftAgentName = 'sql agent plotter langchain (gpt-4o-2024-05-13)';
        rightAgentName = 'sql agent plotter llamaindex (gpt-4o-2024-05-13)';
        break;
      default:
        break;
    }

    const leftAgent = agents.find(agent => agent.name === leftAgentName);
    const rightAgent = agents.find(agent => agent.name === rightAgentName);

    if (leftAgent && rightAgent) {
      setLeftExecutedCode(leftAgent.code.replace('Enter Goal/Prompt Here', goal));
      setRightExecutedCode(rightAgent.code.replace('Enter Goal/Prompt Here', goal));
      setLeftAgent(leftAgent);
      setRightAgent(rightAgent);
    }
  };

  return (
    <Container className="d-flex flex-column align-items-center">
      <div className="w-100 mb-4 d-flex justify-content-between align-items-center">
        <h1 className="text-center mb-0" style={{ color: '#ffffff', flexGrow: 1 }}>LLM Agent Arena</h1>
      </div>
      <p className="text-center mb-4">
        Welcome to the LLM Agent Arena. Here, you can pit two agents against each other based on a goal you provide. 
        You can also head to your profile to save prompts for agents and visit the Prompt Hub to see prompts used by 
        other users along with their ratings.
      </p>
      <Row className="mb-4 w-100">
        <Col className="d-flex justify-content-center align-items-center">
          <Form.Control
            type="text"
            placeholder={displayedPrompt || "Enter your goal"}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            style={{ width: '60%', marginRight: '10px' }}
          />
          <Button variant="primary" onClick={handleSearch}>
            Search
          </Button>
        </Col>
      </Row>
      <Row className="mb-4 w-100">
        <Col className="d-flex justify-content-center align-items-center">
          <Button variant="info" onClick={() => setExample(1)} className="mx-2">Search Example</Button>
          <Button variant="info" onClick={() => setExample(2)} className="mx-2">Stock Example</Button>
          <Button variant="info" onClick={() => setExample(3)} className="mx-2">SQL Plotter Example</Button>
        </Col>
      </Row>
      <Row className="justify-content-center w-100">
        <Col md={5}>
          <h2 className="text-center">Agent 1</h2>
          <AgentDropdown agents={agents} selectedAgent={leftAgent} onSelect={handleLeftSelect} />
          {leftAgent ? (
            <CodeEditor
              agentId={leftAgent._id}
              initialCode={leftExecutedCode}
              onExecute={(code, output) => {
                setLeftExecutedCode(code);
                setLeftOutput(output);
                setLeftCompleted(true);
              }}
              output={leftOutput}
              allowsFileUpload={leftAgent.allowsFileUpload}
              fileUploadMessage={leftAgent.fileUploadMessage}
              dbFilePath={leftAgent.allowsFileUpload ? leftFile : null}
              isExample3={isExample3}
              modificationNeeded={leftAgent.modificationNeeded}
              agentName={leftAgent.name}
            />
          ) : (
            <CodeEditor
              agentId={null}
              initialCode={leftExecutedCode}
              onExecute={(code, output) => {
                setLeftExecutedCode(code);
                setLeftOutput(output);
                setLeftCompleted(true);
              }}
              output={leftOutput}
              allowsFileUpload={false}
              fileUploadMessage={''}
              dbFilePath={null}
              isExample3={isExample3}
              modificationNeeded={false}
            />
          )}
        </Col>
        <Col md={5}>
          <h2 className="text-center">Agent 2</h2>
          <AgentDropdown agents={agents} selectedAgent={rightAgent} onSelect={handleRightSelect} />
          {rightAgent ? (
            <CodeEditor
              agentId={rightAgent._id}
              initialCode={rightExecutedCode}
              onExecute={(code, output) => {
                setRightExecutedCode(code);
                setRightOutput(output);
                setRightCompleted(true);
              }}
              output={rightOutput}
              allowsFileUpload={rightAgent.allowsFileUpload}
              fileUploadMessage={rightAgent.fileUploadMessage}
              dbFilePath={rightAgent.allowsFileUpload ? rightFile : null}
              isExample3={isExample3}
              modificationNeeded={rightAgent.modificationNeeded}
              agentName={rightAgent.name}
            />
          ) : (
            <CodeEditor
              agentId={null}
              initialCode={rightExecutedCode}
              onExecute={(code, output) => {
                setRightExecutedCode(code);
                setRightOutput(output);
                setRightCompleted(true);
              }}
              output={rightOutput}
              allowsFileUpload={false}
              fileUploadMessage={''}
              dbFilePath={null}
              isExample3={isExample3}
              modificationNeeded={false}
            />
          )}
        </Col>
      </Row>
      <Row className="mt-4 w-100">
        <Col className="text-center">
          <Button
            variant="success"
            onClick={() => handleRating('A is better')}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            A is better
          </Button>
          <Button
            variant="success"
            onClick={() => handleRating('B is better')}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            B is better
          </Button>
          <Button
            variant="info"
            onClick={() => handleRating('Tie')}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            Tie
          </Button>
          <Button
            variant="danger"
            onClick={() => handleRating('Both are bad')}
            className="mx-3 my-2"
            disabled={!ratingEnabled || hasVoted}
          >
            Both are bad
          </Button>
        </Col>
      </Row>
      {hasVoted && isLoggedIn && (
        <Row className="mt-4 justify-content-center w-100">
          <Col className="text-center">
            <Button variant="primary" onClick={handleSavePrompt} className="mt-2">
              Save Prompt
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                navigator.clipboard.writeText(shareURL);
                toast.success('Result link copied to clipboard');
              }}
              className="mt-2"
              disabled={!shareURL}
            >
              Share Result
            </Button>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default AgentArena;
