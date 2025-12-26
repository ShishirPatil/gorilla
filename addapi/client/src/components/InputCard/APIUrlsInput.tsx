// APIUrlsInput.tsx
import React, { useCallback } from 'react';

interface APIUrlsInputProps {
  urls: string[];
  setUrls: React.Dispatch<React.SetStateAction<string[]>>;
}

const APIUrlsInput: React.FC<APIUrlsInputProps> = ({ urls, setUrls }) => {
  // Function to add an empty URL field to the list
  const handleAddMoreUrls = useCallback(() => {
    setUrls((prevUrls) => [...prevUrls, '']);
  }, [setUrls]);

  // Function to remove a URL field from the list
  const handleDeleteUrl = useCallback((index: number) => {
    setUrls((prevUrls) => prevUrls.filter((_, idx) => idx !== index));
  }, [setUrls]);

  return (
    <div className="form-group">
      <label htmlFor="api_urls">API URLs:</label>
      {urls.map((url, index) => (
        <div key={index} className="input-group mb-2">
          <input
            type="text"
            className="form-control api-url"
            id={`api_url_${index}`}
            value={url}
            onChange={(e) => {
              const newUrls = [...urls];
              newUrls[index] = e.target.value;
              setUrls(newUrls); // Updates the URL at the specific index with user input
            }}
            placeholder={`API URL ${index + 1}`}
            aria-label={`API URL ${index + 1}`}
          />
          <div className="input-group-append">
            {
              index > 0 ? (  // Only show delete button if it's not the first URL field
                <button
                  className="btn btn-danger"
                  type="button"
                  onClick={() => handleDeleteUrl(index)}
                  aria-label="Delete URL">
                  &times;
                </button>
              ) :
                <button
                  className="btn btn-info"
                  type="button"
                  onClick={handleAddMoreUrls} // Button to add more URL fields
                  aria-label="Add more URLs"
                >+</button>
            }
          </div>
        </div>
      ))}
    </div>
  );
};

export default APIUrlsInput;
