import React from 'react';
import AceEditor from 'react-ace';
import 'ace-builds/src-noconflict/mode-python';
import 'ace-builds/src-noconflict/theme-monokai';
import { Card } from 'react-bootstrap';

const StaticCodeEditor = ({ executedCode, output }) => {
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
        />
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
      </Card.Body>
    </Card>
  );
};

export default StaticCodeEditor;
