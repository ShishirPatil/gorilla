// InputCard.tsx
import React, { useState } from 'react';
import InputField from './InputField';
import APIUrlsInput from './APIUrlsInput';
import { useDashboard } from '../../context/DashboardContext';
import { convertUrls } from '../../api/apiService';
import { toast } from 'react-toastify';
import validator from 'validator';


const InputCard = () => {
  const {
    username, setUsername,
    apiName, setApiName,
    urls, setUrls,
    setUrlsResults
  } = useDashboard();

  const [isLoading, setIsLoading] = useState(false);

  const isFormValid = () => {
    if (username.trim() === '' || apiName.trim() === '') {
      toast.error("Username and API Name are required.");
      return false;
    }

    // Collect indices of all invalid URLs
    const invalidUrlsIndices = urls
      .map((url, index) => ({ index, isValid: url.trim() !== '' && validator.isURL(url) }))
      .filter(({ isValid }) => !isValid)
      .map(({ index }) => index);

    // If there are any invalid URLs, display their indices
    if (invalidUrlsIndices.length > 0) {
      const plural = invalidUrlsIndices.length > 1 ? 's' : '';
      const invalidUrlsMessage = `Invalid URL${plural} at index${plural}: ${invalidUrlsIndices.join(', ')}.`;
      toast.error(invalidUrlsMessage);
      return false;
    }
    return true;
  };

  const saveToLocalStorage = (userName: string, apiName: string) => {
    localStorage.setItem('username', userName);
    localStorage.setItem('apiName', apiName);
  };

  const handleConvert = async (event: React.MouseEvent) => {
    event.preventDefault();
    if (isFormValid()) {
      setIsLoading(true);
      setUrlsResults({});
      saveToLocalStorage(username, apiName);
      try {
        const result = await toast.promise(convertUrls(username, apiName, urls.filter(url => url.trim() !== '')),
          {
            pending: "Converting URLs...",
            success: "URLs converted successfully!",
            error: "Conversion failed.",
          });
        setUrlsResults(result);
      } catch (error) {
        console.error(error);
      }
      setIsLoading(false);
    };
  };

  const handleClear = () => {
    setUsername('');
    setApiName('');
    setUrls(['']);
    setUrlsResults({});
  };

  return (
    <div className="card border-primary shadow-lg">
      <div className="card-header bg-light">
        <h4>API Information</h4>
      </div>
      <div className="card-body">
        <InputField label="Github Username" id="user_name" type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
        <InputField label="API Name" id="api_name" type="text" value={apiName} onChange={(e) => setApiName(e.target.value)} />
        <APIUrlsInput urls={urls} setUrls={setUrls} />
      </div>
      <div className="card-footer d-flex justify-content-around">
        <button
          className="btn btn-db btn-grey"
          onClick={handleClear}
        >
          Clear
        </button>
        <button
          className="btn btn-db btn-convert"
          onClick={handleConvert}
          disabled={isLoading}
          aria-busy={isLoading}
          aria-live="polite"
        >
          {isLoading ? "Loading..." : "Convert"}
        </button>
      </div>
    </div>
  );
};

export default InputCard;
