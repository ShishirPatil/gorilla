import React, { useState, useEffect, useContext } from 'react';
import AceEditor from 'react-ace';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/theme-monokai';
import 'ace-builds/src-noconflict/theme-github';
import axios from 'axios';
import { Card, Button, Spinner, Form, Collapse } from 'react-bootstrap';
import StaticFileInput from './StaticFileInput';
import { ThemeContext } from '../App';
import { AnsiUp } from 'ansi_up';

const ansiUp = new AnsiUp();

const CodeEditor = ({
  agentId,
  initialCode,
  onExecute,
  output: initialOutput,
  allowsFileUpload,
  fileUploadMessage,
  dbFilePath,
  isExample3,
  modificationNeeded,
  agentName,
  averageExecutionTime,
  file,
  userApiKeys,
  codeCollapsed,
  setCodeCollapsed,
  isRunningBoth,
  runBothTriggered,
  onCodeChange,
  completed,
}) => {
  const { theme } = useContext(ThemeContext);
  const [code, setCode] = useState(initialCode || '');
  const [output, setOutput] = useState(initialOutput || '');
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [input, setInput] = useState('');
  const [dbFileName, setDbFileName] = useState(dbFilePath ? dbFilePath.name : '');
  const [dbFile, setDbFile] = useState(dbFilePath ? dbFilePath : null);
  const [generalFileName, setGeneralFileName] = useState('');
  const [generalFile, setGeneralFile] = useState(file ? file : null);
  const [countdown, setCountdown] = useState(0);
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [imageSrc, setImageSrc] = useState('');
  const [imageLoading, setImageLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [showRunButton, setShowRunButton] = useState(false);
  const [eventSource, setEventSource] = useState(null); // Added state variable for EventSource


  

  useEffect(() => {
    setCode(initialCode || '');
  }, [initialCode]);

  useEffect(() => {
    setOutput(initialOutput || '');
  }, [initialOutput]);

  useEffect(() => {
    if (file) {
      setGeneralFile(file);
      setGeneralFileName(file.name);
    }
  }, [file]);

  useEffect(() => {
    if (dbFilePath && dbFilePath instanceof File) {
      setDbFile(dbFilePath);
      setDbFileName(dbFilePath.name);
    }
  }, [dbFilePath]);

  useEffect(() => {
    if (allowsFileUpload && file) {
      setGeneralFile(file);
      setGeneralFileName(file.name);
    }
  }, [allowsFileUpload, file]);

  useEffect(() => {
    if (isExample3 && file) {
      setGeneralFile(file);
      setGeneralFileName(file.name);
    }
  }, [isExample3, file]);

  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setInterval(() => {
        setCountdown((prevCountdown) => prevCountdown - 1);
      }, 1000);
    } else {
      clearInterval(timer);
    }
    return () => clearInterval(timer);
  }, [countdown]);

  const handleCodeChange = (newCode) => {
    setCode(newCode);
    if (onCodeChange) {
      onCodeChange(newCode);
    }
  };

  useEffect(() => {
    if (isExample3) {
      setGeneralFileName('mydata.csv');
    }
  }, [isExample3]);

  useEffect(() => {
    if (runBothTriggered && isRunningBoth && !completed) {
      const avgExecTime = parseInt(averageExecutionTime, 10);
      let countdownTime = avgExecTime >= 5 ? avgExecTime : 40;
      setCountdown(countdownTime);
      setShowRunButton(true);
      setLoading(true);
    } else if (completed) {
      setLoading(false);
      setCountdown(0);
      setShowRunButton(false);
    }
  }, [runBothTriggered, isRunningBoth, completed, averageExecutionTime]);

  const handleDbFileChange = (event) => {
    const file = event.target.files[0];
    setDbFile(file);
    setDbFileName(file.name);
  };

  const handleGeneralFileChange = (event) => {
    const file = event.target.files[0];
    setGeneralFileName(file.name);
    setGeneralFile(file);
  };

  useEffect(() => {
    if (generalFileName && code.includes('FILE_NAME')) {
      const updatedCode = code.replace(/FILE_NAME/g, generalFileName);
      setCode(updatedCode);
      if (onCodeChange) {
        onCodeChange(updatedCode);
      }
    }
  }, [generalFileName, code]);

  const handleRunCode = () => {
    // Close any existing EventSource
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }

    setLoading(true);
    setIsRunning(true);
    setOutput('');
    setCodeCollapsed(true);

    const avgExecTime = parseInt(averageExecutionTime, 10);
    let countdownTime = avgExecTime >= 5 ? avgExecTime : 40;
    setCountdown(countdownTime);

    const formData = new FormData();
    formData.append('code', code);
    formData.append('agentId', agentId);

    // File handling logic (unchanged)

    if (userApiKeys) {
      Object.keys(userApiKeys).forEach((key) => {
        formData.append(key, userApiKeys[key]);
      });
    }

    axios
      .post('https://agent-arena-location.onrender.com/api/jobs/create', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((response) => {
        setJobId(response.data.jobId);
        streamJobOutput(response.data.jobId);
      })
      .catch((error) => {
        setOutput(error.response?.data?.error || 'An error occurred');
        setLoading(false);
        setIsRunning(false);
      });
  };

  const streamJobOutput = (jobId) => {
    const es = new EventSource(`https://agent-arena-location.onrender.com/api/jobs/${jobId}/stream`);
    setEventSource(es); // Store the EventSource

    let fullOutput = '';

    es.onmessage = (event) => {
      let processedOutput = event.data;
      const coloredHtml = ansiUp.ansi_to_html(processedOutput);
      fullOutput += coloredHtml + '\n';
      setOutput((prevOutput) => prevOutput + coloredHtml + '\n');
    };

    es.onerror = () => {
      es.close();
      setLoading(false);
      setIsRunning(false);
      setCountdown(0);
      if (onExecute) {
        onExecute(code, fullOutput);
      }
    };

    es.addEventListener('end', () => {
      es.close();
      setLoading(false);
      setIsRunning(false);
      setCountdown(0);
      if (onExecute) {
        onExecute(code, fullOutput);
      }
    });
  };

  const handleProvideInput = () => {
    axios
      .post(`https://agent-arena-location.onrender.com/api/jobs/${jobId}/input`, { input })
      .then((response) => {
        setInput('');
      })
      .catch((error) => {
        console.error('Error providing input:', error);
      });
  };

  // **Add useEffect to reset state when agentId changes**
  useEffect(() => {
    // Reset code to initialCode
    setCode(initialCode || '');
    // Reset output
    setOutput(initialOutput || '');
    // Reset loading and execution states
    setLoading(false);
    setIsRunning(false);
    setCountdown(0);
    setShowRunButton(false);
    // Close any existing EventSource connections
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    // Reset jobId
    setJobId(null);
    // Reset files if necessary
    setDbFile(dbFilePath ? dbFilePath : null);
    setDbFileName(dbFilePath ? dbFilePath.name : '');
    setGeneralFile(file ? file : null);
    setGeneralFileName(file ? file.name : '');
    // Reset any other state variables as needed
  }, [agentId]);

  // **Cleanup on component unmount**
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  return (
    <Card className="mt-3">
      <Card.Body>
        {agentId && !isRunning && !isRunningBoth && (
          <div
            className={`alert ${
              isExample3 ? 'alert-info' : modificationNeeded ? 'alert-warning' : 'alert-info'
            } py-1`}
            role="alert"
          >
            {isExample3 || !modificationNeeded ? (
              <>
                We have populated API keys for agents, but for the best experience, and if you encounter rate limits,
                pass your API keys and run the code. You can add API keys <a href="/profile">here</a>.
              </>
            ) : (
              <>
                Modify the task description in the code. We have populated API keys, but for the best experience, and if
                you encounter rate limits, add your API keys&nbsp;
                <a href="/profile">here</a>.
              </>
            )}
          </div>
        )}
        {completed && (
          <Button
            onClick={() => setCodeCollapsed(!codeCollapsed)}
            aria-controls="code-collapse"
            aria-expanded={!codeCollapsed}
            className="mb-3"
          >
            {codeCollapsed ? 'Show Code' : 'Hide Code'}
          </Button>
        )}
        <Collapse in={!codeCollapsed}>
          <div id="code-collapse">
            <AceEditor
              mode="python"
              theme={theme === 'dark' ? 'monokai' : 'github'}
              value={code}
              onChange={handleCodeChange}
              name={`editor_${agentId}`}
              editorProps={{ $blockScrolling: true }}
              width="100%"
              height="300px"
              readOnly={!modificationNeeded} // Make the editor non-editable unless modification is needed
            />
          </div>
        </Collapse>
        <div className="text-center w-100 mt-2">
          {showRunButton && (
            <div className="text-center mt-3">
              <Button variant="primary" disabled>
                <Spinner animation="border" size="sm" />
                <span className="ms-2">{countdown > 0 ? `${countdown}s ` : 'Running...'}</span>
              </Button>
            </div>
          )}
        </div>
        {input && (
          <Form>
            <Form.Group controlId="formInput">
              <Form.Label>Input Required:</Form.Label>
              <Form.Control
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <Button variant="primary" onClick={handleProvideInput} className="mt-2">
                Submit Input
              </Button>
            </Form.Group>
          </Form>
        )}

        {allowsFileUpload && (
          <>
            {/* Static file input that automatically shows the file name */}
            {!generalFile && (
              <div className="alert alert-warning mt-2">
                <strong>Warning:</strong> You must upload a file for this agent to run.
              </div>
            )}
          </>
        )}
        <Card.Text
          as="pre"
          className="pre mt-3"
          style={{
            maxHeight: '500px',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            padding: '15px',
            borderRadius: '4px',
            fontSize: '1.1em',
            backgroundColor: theme === 'dark' ? '#2d2d2d' : '#f8f9fa',
            color: theme === 'dark' ? '#ffffff' : '#000000',
          }}
          dangerouslySetInnerHTML={{ __html: output }}
        />

        {imageSrc && (
          <div className="mt-3">
            <img src={imageSrc} alt="Generated Base64 Image" style={{ maxWidth: '100%', height: 'auto' }} />
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default CodeEditor;
