import React from 'react';
import AceEditor from 'react-ace';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/theme-monokai';
import { Card } from 'react-bootstrap';
import DOMPurify from 'dompurify';

const StaticCodeEditor = ({ executedCode, output }) => {
  // Function to safely set HTML content
  const createMarkup = (html) => {
    return {__html: DOMPurify.sanitize(html)};
  }

  return (
    <Card className="mt-3">
      <Card.Body>
        <AceEditor
          mode="python"
          theme="monokai"
          value={executedCode}
          readOnly={true}
          name="static_code_editor"
          editorProps={{ $blockScrolling: true }}
          width="100%"
          height="300px"
          fontSize="14px"
          setOptions={{
            fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace",
          }}
        />
        <pre 
          className="mt-3" 
          style={{
            maxHeight: '500px',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            padding: '15px',
            borderRadius: '4px',
            fontSize: '1.1em',
            backgroundColor: '#2d2d2d' ,
            color:  '#ffffff',
          }}
          dangerouslySetInnerHTML={createMarkup(output)}
        />
      </Card.Body>
    </Card>
  );
};

export default StaticCodeEditor;