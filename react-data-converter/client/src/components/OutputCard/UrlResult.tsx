import React, { useState, useCallback } from 'react';
import { ConvertedURL } from '../../types/types';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import UrlResultItem from './UrlResultItem';

interface UrlResultProps {
  result: ConvertedURL;
  onResultsChange: (updatedResults: ConvertedURL) => void;
}


const UrlResult: React.FC<UrlResultProps> = React.memo(({ result, onResultsChange }) => {
  const [editableIndex, setEditableIndex] = useState<number | null>(null);
  const [editedJSONResults, setEditedDetails] = useState<string[]>(result.data.map(detail => JSON.stringify(detail, null, 2)));


  const toggleEdit = (index: number) => {
    setEditableIndex(prevIndex => prevIndex === index ? null : index);
  };


  const handleCopy = async (text: string, apiName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${apiName} Details Copied!`);
    } catch (err) {
      toast.error('Failed to copy');
    }
  };


  // Update jsonOutput state when textarea content changes
  const handleChange = (value: string, index: number) => {
    const updatedJSONResults = [...editedJSONResults];
    updatedJSONResults[index] = value;
    setEditedDetails(updatedJSONResults);
  };

  const handleBlur = () => {
    try {
      const updatedDetails = editedJSONResults.map(detail => JSON.parse(detail));
      onResultsChange({ ...result, data: updatedDetails }); // Notify OutputCard of the change
    } catch (error) {
      toast.error("Invalid JSON format.");
    }
  };


  return (
    <div className="mb-4">
      <p>Status: {result.status}{' '}
        {result.status === 'success' ? (
          <span style={{ height: '10px', width: '10px', backgroundColor: 'green', borderRadius: '50%', display: 'inline-block' }}></span>
        ) : (
          <span style={{ height: '10px', width: '10px', backgroundColor: 'red', borderRadius: '50%', display: 'inline-block' }}></span>
        )}
      </p>
      {result.data.map((value, index) => (
        <UrlResultItem
          key={index} // TODO: Consider using a more stable identifier
          value={value}
          index={index}
          editableIndex={editableIndex}
          toggleEdit={toggleEdit}
          handleCopy={handleCopy}
          editedJSONResults={editedJSONResults}
          handleChange={handleChange}
          handleBlur={handleBlur}
        />
      ))}
      {/* <ToastContainer position="top-center" autoClose={800} /> */}
    </div>
  );
});

UrlResult.displayName = 'UrlResult';
export default UrlResult;
