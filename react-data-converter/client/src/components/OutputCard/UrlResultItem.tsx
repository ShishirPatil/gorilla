import React from 'react';
import IconButton from './IconButton';
import { faEdit, faClipboard } from '@fortawesome/free-solid-svg-icons';
import { ApiCallDetail } from '@/types/types';


interface UrlResultItemProps {
    value: ApiCallDetail;
    index: number;
    editableIndex: number | null;
    toggleEdit: (index: number) => void;
    handleCopy: (text: string, apiName: string) => void;
    editedJSONResults: string[];
    handleChange: (event: React.ChangeEvent<HTMLTextAreaElement>, index: number) => void;
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
    <div className='card-body'>
        <div className="d-flex justify-content-between align-items-center">
            <h5 className="card-title">{value.api_name}</h5>
            <div>
                <IconButton icon={faEdit} onClick={() => toggleEdit(index)} ariaLabel="Edit" />
                <IconButton icon={faClipboard} onClick={() => handleCopy(editedJSONResults[index], value.api_name)} ariaLabel="Copy" />
            </div>
        </div>
        <textarea
            className="form-control mt-2"
            rows={7}
            value={editedJSONResults[index]}
            readOnly={editableIndex !== index}
            onChange={(e) => handleChange(e, index)}
            onBlur={() => handleBlur()}
        />
    </div>
);

export default UrlResultItem;