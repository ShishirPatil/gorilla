// InputCard.tsx
import React, { useState, useEffect } from 'react';
import InputField from './InputField';
import APIUrlsInput from './APIUrlsInput';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import validator from 'validator';

// InputCard.tsx
interface InputCardProps {
  handleConvertAndSetUrls: (username: string, apiName: string, urls: string[]) => void;
}

const InputCard: React.FC<InputCardProps> = ({ handleConvertAndSetUrls }) => {
  const [username, setUsername] = useState('');
  const [apiName, setApiName] = useState('');
  const [urls, setUrls] = useState<string[]>(['']);
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



  const handleConvert = async (event: React.MouseEvent) => {
    event.preventDefault();
    if (isFormValid()) {
      setIsLoading(true);
      await handleConvertAndSetUrls(username, apiName, urls.filter(url => url.trim() !== ''));
      setIsLoading(false);
    };
  };

  return (
    <div className="card border-primary shadow-lg">
      <div className="card-header bg-primary text-white">
        <h4>Option 2 JSON Input</h4>
      </div>
      <div className="card-body">
        <InputField label="User Name" id="user_name" type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
        <InputField label="API Name" id="api_name" type="text" value={apiName} onChange={(e) => setApiName(e.target.value)} />
        <APIUrlsInput urls={urls} setUrls={setUrls} />
      </div>
      <div className="card-footer d-flex justify-content-around">
        <button
          className="btn btn-primary"
          onClick={handleConvert}
          disabled={isLoading}
          aria-busy={isLoading}
          aria-live="polite"
        >
          {isLoading ? "Loading..." : "Convert"}
        </button>
      </div>
      <ToastContainer
        position="top-right"
        autoClose={1500}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
    </div>
  );
};

export default InputCard;
