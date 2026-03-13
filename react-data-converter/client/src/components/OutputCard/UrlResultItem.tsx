import React from 'react';
import IconButton from './IconButton';
import { faEdit, faClipboard } from '@fortawesome/free-solid-svg-icons';
import { ApiCallDetail } from '@/types/types';
import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';

interface UrlResultItemProps {
    value: ApiCallDetail;
    index: number;
    editableIndex: number | null;
    toggleEdit: (index: number) => void;
    handleCopy: (text: string, apiName: string) => void;
    editedJSONResults: string[];
    handleChange: (value: string, index: number) => void; // Updated to reflect CodeMirror's onChange signature
    handleBlur: () => void;
}

const UrlResultItem: React.FC<UrlResultItemProps> = ({
    value,
    index,
    editableIndex,
    toggleEdit,
    handleCopy,
    editedJSONResults,
    handleChange,
    handleBlur
}) => (
    <div className='card mb-3'>
        <div className="card-body">
            <div className="d-flex justify-content-between align-items-center">
                <h5 className="card-title">{value.api_name}</h5>
                <div>
                    <IconButton icon={faEdit} onClick={() => toggleEdit(index)} ariaLabel="Edit" />
                    <IconButton icon={faClipboard} onClick={() => handleCopy(editedJSONResults[index], value.api_name)} ariaLabel="Copy" />
                </div>
            </div>
            <CodeMirror
                value={editedJSONResults[index]}
                extensions={[json()]}
                onChange={(value) => handleChange(value, index)}
                onBlur={handleBlur}
                editable={editableIndex !== index}
                height="auto"
                minHeight="100px"
                basicSetup={{
                    lineNumbers: false,
                    closeBrackets: true,
                }}
                style={{ fontSize: '14px', borderRadius: '4px', border: '1px solid #ced4da' }} 
            />
        </div>
    </div>
);

export default UrlResultItem;
