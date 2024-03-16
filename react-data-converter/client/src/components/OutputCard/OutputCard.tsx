import React, { useState, useCallback, useEffect } from 'react';
import UrlResult from './UrlResult';
import { ConvertResult, ConvertedURL, ApiCallDetail } from '../../types/types';
import IconButton from './IconButton';
import { raisePullRequest, reportIssue } from '../../pages/api/apiService';
import { faThumbsDown, faSyncAlt } from '@fortawesome/free-solid-svg-icons';
import { convertUrls } from '../../pages/api/apiService';
import { toast } from 'react-toastify';

// OutputCard.tsx
interface OutputCardProps {
  urlsResults: ConvertResult;
}

const OutputCard: React.FC<OutputCardProps> = ({ urlsResults }) => {
  const [editedResults, setEditedResults] = useState<ConvertResult>(urlsResults);

  useEffect(() => {
    setEditedResults(urlsResults);
  }, [urlsResults]);

  const handleResultsChange = ((url: string, updatedResult: ConvertedURL) => {
    setEditedResults(prev => ({
      ...prev,
      [url]: updatedResult,
    }));
  });

  const handleRaisePullRequest = async () => {
    try {
      await raisePullRequest(editedResults);
    } catch (error) {
      alert(`An error occurred while storing Option1 content: ${error}`);
    }
  };

  const handleReportIssue = (url: string, result: ConvertedURL) => {
    reportIssue(url, result);
  };

  // Function to handle regeneration of a single URL
  const handleRegenerateUrl = async (urlToRegenerate: string) => {
    setEditedResults(prevResults => ({
      ...prevResults,
      [urlToRegenerate]: { status: "loading", data: [] },
    }));
    try {
      // TODO: Replace "username" and "apiName" with actual values or state
      const result = await toast.promise(convertUrls("username", "apiName", [urlToRegenerate]), {
        pending: "Regenerating URL...",
        success: "URL regenerated successfully!",
        error: "Failed to regenerate URL",
      });
      setEditedResults(prevResults => ({
        ...prevResults,
        [urlToRegenerate]: result[urlToRegenerate],
      }));

    } catch (error) {
      console.error("Failed to regenerate URL:", error);
    }
  };

  const renderUrlResults = (urlResults: ConvertResult) => {
    if (Object.keys(urlResults).length === 0) {
      return <p>No results to display.</p>;
    }

    return Object.entries(urlResults).map(([url, convertedURL]) => (
      <div key={url}>
        <div className="d-flex justify-content-between align-items-center">
          <h5>{url}</h5>
          <div>
            <IconButton icon={faSyncAlt} onClick={() => { handleRegenerateUrl(url); }} ariaLabel="Regenerate" />
            <IconButton icon={faThumbsDown} onClick={() => { handleReportIssue(url, convertedURL); }} ariaLabel="Dislike" className='btn-danger' />
          </div>
        </div>
        <UrlResult
          result={convertedURL}
          onResultsChange={(updatedResult) => handleResultsChange(url, updatedResult)}
        />
      </div>
    ));
  };


  return (
    <div className="card border-secondary shadow-lg">
      <div className="card-header bg-secondary text-white">
        <h4>JSON Outputs</h4>
      </div>
      <div className="card-body">
        {renderUrlResults(editedResults)}
      </div>
      <div className="card-footer d-flex justify-content-around">
        <button className="btn btn-primary" onClick={handleRaisePullRequest}>Raise Pull Request</button>
      </div>
    </div>
  );
};

export default OutputCard;
