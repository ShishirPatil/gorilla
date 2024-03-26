import React, { useState, useCallback } from 'react';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SaveIcon from '@mui/icons-material/Save';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { ApiCallDetail } from '../../types/types';
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
}) => {
    // State to manage the copied status of the item to change Icons
    const [isCopied, setIsCopied] = useState(false);

    const handleCopyWrap = useCallback((text: string, apiName: string) => {
        handleCopy(text, apiName);
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
    }, [handleCopy]);

    return (
        <div className='card mb-3'>
            <div className="card-body">
                <div className="d-flex justify-content-between align-items-center">
                    <h5 className="card-title">{value.api_name}</h5>
                    <div>
                        <IconButton onClick={() => toggleEdit(index)} aria-label={editableIndex === index ? "Save" : "Edit"} size="small">
                            {editableIndex === index ? <SaveIcon fontSize="small" /> : <EditIcon fontSize="small" />}
                        </IconButton>
                        <IconButton aria-label={isCopied ? "Copied" : "Copy"} size="small" onClick={!isCopied ? () => handleCopyWrap(editedJSONResults[index], value.api_name) : undefined}>
                            {isCopied ? <CheckCircleIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
                        </IconButton>
                    </div>
                </div>
                <CodeMirror
                    value={editedJSONResults[index]}
                    extensions={[json()]}
                    onChange={(value) => handleChange(value, index)}
                    onBlur={handleBlur}
                    editable={editableIndex === index}
                    height="auto"
                    minHeight="100px"
                    basicSetup={{
                        lineNumbers: false,
                        closeBrackets: true,
                    }}
                    style={{
                        fontSize: '11px',
                        borderRadius: '4px',
                        border: '1px solid #ced4da',
                        // Add a shadow to make it pop out more when editable
                        boxShadow: editableIndex === index ? '0 0 8px rgba(0, 0, 0, 0.5)' : 'none',
                    }}
                />
            </div>
        </div>
    );
};

export default React.memo(UrlResultItem);
