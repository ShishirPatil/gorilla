import React, { useState, useEffect } from 'react';
import UrlResult from './UrlResult';
import { ConvertResult, ConvertedURL } from '../../types/types';
import IconButton from './IconButton';
import { faThumbsDown, faSyncAlt } from '@fortawesome/free-solid-svg-icons';
import { convertUrls, raisePullRequest, reportIssue } from '../../api/apiService';
import { toast } from 'react-toastify';
import { useDashboard } from '../../context/DashboardContext';

// OutputCard.tsx
interface OutputCardProps {

}

const OutputCard: React.FC<OutputCardProps> = () => {
  const { urlsResults, username, apiName } = useDashboard();
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
      await raisePullRequest(username, editedResults);
    } catch (error) {
      alert(`An error while raising a pull request: ${error}`);
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
      const result = await toast.promise(convertUrls(username, apiName, [urlToRegenerate]), {
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
          <h5 className="text-truncate" style={{ maxWidth: '80%' }} title={url}>{url}</h5>
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
    <div className="card border-primary shadow-lg">
      <div className="card-header bg-light">
        <h4>Results</h4>
      </div>
      <div className="card-body">
        {renderUrlResults(editedResults)}
      </div>
      <div className="card-footer d-flex justify-content-around">
        <button className="btn btn-db btn-grey" onClick={handleRaisePullRequest}>Raise Pull Request</button>
      </div>
    </div>
  );
};

export default OutputCard;
