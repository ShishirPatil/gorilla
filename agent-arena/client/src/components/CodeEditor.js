import React, { useState, useEffect, useContext } from 'react';
import AceEditor from 'react-ace';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/theme-monokai';
import 'ace-builds/src-noconflict/theme-github'; // Add this for light mode
import axios from 'axios';
import { Card, Button, Spinner, Form } from 'react-bootstrap';
import StaticFileInput from './StaticFileInput';
import { ThemeContext } from '../App';

const CodeEditor = ({ agentId, initialCode, onExecute, output: initialOutput, allowsFileUpload, fileUploadMessage, dbFilePath, isExample3, modificationNeeded, agentName }) => {
  const { theme } = useContext(ThemeContext);
  const [code, setCode] = useState(initialCode || '');
  const [output, setOutput] = useState(initialOutput || '');
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [input, setInput] = useState('');
  const [dbFileName, setDbFileName] = useState(dbFilePath ? dbFilePath.name : '');
  const [dbFile, setDbFile] = useState(dbFilePath ? dbFilePath : null);
  const [generalFileName, setGeneralFileName] = useState('');
  const [generalFile, setGeneralFile] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [imageSrc, setImageSrc] = useState('');
  const [imageLoading, setImageLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setCode(initialCode);
  }, [initialCode]);

  useEffect(() => {
    setOutput(initialOutput);
  }, [initialOutput]);

  useEffect(() => {
    if (dbFilePath && dbFilePath instanceof File) {
      setDbFile(dbFilePath);
      setDbFileName(dbFilePath.name);
    }
  }, [dbFilePath]);

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
  };

  const handleDbFileChange = (event) => {
    const file = event.target.files[0];
    setDbFile(file);
    setDbFileName(file.name);
    console.log("DB file set:", file);
  };

  const handleGeneralFileChange = (event) => {
    const file = event.target.files[0];
    setGeneralFileName(file.name);
    setGeneralFile(file);
    console.log("General file set:", file);
  };

  const handleRunCode = () => {
    setLoading(true);
    setCountdown(20);
    const formData = new FormData();
    formData.append('code', code);
    formData.append('agentId', agentId);
    console.log(agentName);
    console.log(dbFile);
    if (["sql agent plotter llamaindex (gpt-4o-2024-08-06)", "sql agent plotter langchain (gpt-4o-2024-08-06)",
    "sql agent plotter llamaindex (gpt-4o-2024-05-13)", "sql agent plotter langchain (gpt-4o-2024-05-13)",
    "sql agent plotter llamaindex (gpt-4-turbo-2024-04-09)", "sql agent plotter langchain (gpt-4-turbo-2024-04-09)",
    "sql agent plotter llamaindex (gpt-4-0613)", "sql agent plotter langchain (gpt-4-0613)",
    "sql agent plotter llamaindex (claude-3-5-sonnet-20240620)", "sql agent plotter langchain (claude-3-5-sonnet-20240620)",
    "sql agent plotter llamaindex (claude-3-opus-20240229)", "sql agent plotter langchain (claude-3-opus-20240229)",
    "sql agent plotter llamaindex (claude-3-haiku-20240307)", "sql agent plotter langchain (claude-3-haiku-20240307)",
    "anthropic sql query"].includes(agentName)) {
      console.log('hi');
      if (dbFile) {
        formData.append('db_file', dbFile);
        console.log("Appending db_file to formData:", dbFile);
      } 
    } else if (generalFile) {
      formData.append('general_file', generalFile);
      console.log("Appending general_file to formData:", generalFile);
    }

    // Log the FormData to ensure it has the correct keys and values
    for (let [key, value] of formData.entries()) {
      console.log(key, value);
    }

    axios.post('https://agent-arena-wuwl.onrender.com/api/jobs/create', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    .then(response => {
      setJobId(response.data.jobId);
      pollJobStatus(response.data.jobId);
    })
    .catch(error => {
      setOutput(error.response?.data?.error || 'An error occurred');
      setLoading(false);
    });
  };

  const pollJobStatus = (jobId) => {
    const interval = setInterval(() => {
      axios.get(`https://agent-arena-wuwl.onrender.com/api/jobs/${jobId}/status`)
        .then(response => {
          setOutput(response.data.output);
          setGeneratedFiles(response.data.generated_files);

          if (response.data.status === 'completed' || response.data.status === 'error') {
            clearInterval(interval);
            setLoading(false);
            setCountdown(0);

            const base64Pattern = /"content":"([A-Za-z0-9+/=]+)"/;
            const match = response.data.output.match(base64Pattern);
            if (match) {
              const base64String = match[1];
              const imageSrc = `data:image/png;base64,${base64String}`;
              setImageSrc(imageSrc);
              setImageLoading(true);
            }

            if (onExecute) {
              onExecute(code, response.data.output);
            }
          }

          if (response.data.currentInput) {
            setInput(response.data.currentInput);
          }
        })
        .catch(error => {
          console.error(error);
          clearInterval(interval);
          setLoading(false);
          setCountdown(0);
        });
    }, 1000);
  };

  const handleProvideInput = () => {
    axios.post(`https://agent-arena-wuwl.onrender.com/api/jobs/${jobId}/input`, { input })
      .then(response => {
        setInput('');
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <Card className="mt-3">
      <Card.Body>
        {agentId && (
          <div className={`alert ${isExample3 ? 'alert-info' : (modificationNeeded ? 'alert-warning' : 'alert-info')} py-1`} role="alert">
            {isExample3 ? "Add your API keys and run the code" : (modificationNeeded ? "Modify the task description in the code and add your API keys" : "Add your API keys and run the code")}
          </div>
        )}
        <AceEditor
          mode="python"
          theme={theme === 'dark' ? 'monokai' : 'github'}
          value={code}
          onChange={handleCodeChange}
          name={`editor_${agentId}`}
          editorProps={{ $blockScrolling: true }}
          width="100%"
          height="300px"
        />
        {allowsFileUpload && (
          <Form.Group controlId="formFile" className="mt-3">
            <Form.Label>{fileUploadMessage}</Form.Label>
            {isExample3 ? (
              <StaticFileInput filename="company.db" />
            ) : (
              <Form.Control type="file" onChange={["sql agent plotter langchain (gpt-4o-2024-05-13)", "sql agent plotter llamaindex (gpt-4o-2024-05-13)"].includes(agentName) ? handleDbFileChange : handleGeneralFileChange} />
            )}
            {["sql agent plotter langchain (gpt-4o-2024-05-13)", "sql agent plotter llamaindex (gpt-4o-2024-05-13)"].includes(agentName) && dbFileName && <div className="mt-2">{}</div>}
          </Form.Group>
        )}
        <div className="text-center w-100 mt-2">
          <Button variant="primary" onClick={handleRunCode} disabled={loading}>
            {loading ? (
              <>
                <Spinner animation="border" size="sm" /> {countdown > 0 ? ` ${countdown}s` : 'Running...'}
              </>
            ) : 'Run Code'}
          </Button>
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
        <Card.Text as="pre" className="pre mt-3" style={{
          maxHeight: '300px',
          overflowY: 'auto',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          padding: '10px',
          borderRadius: '4px'
        }}>
          {output}
        </Card.Text>
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
