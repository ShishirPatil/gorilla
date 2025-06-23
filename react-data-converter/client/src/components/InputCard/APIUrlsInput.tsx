// APIUrlsInput.tsx
import React from 'react';

interface APIUrlsInputProps {
  urls: string[];
  setUrls: React.Dispatch<React.SetStateAction<string[]>>;
}

const APIUrlsInput: React.FC<APIUrlsInputProps> = ({ urls, setUrls }) => {
  const handleAddMoreUrls = () => {
    setUrls((prevUrls) => [...prevUrls, '']);
  };

  const handleDeleteUrl = (index: number) => {
    setUrls((prevUrls) => prevUrls.filter((_, idx) => idx !== index));
  };

  return (
    <div className="form-group">
      <label htmlFor="api_urls">API URLs:</label>
      {urls.map((url, index) => (
        <div key={index} className="input-group mb-2">
          <input
            type="text"
            className="form-control api-url"
            value={url}
            onChange={(e) => {
              const newUrls = [...urls];
              newUrls[index] = e.target.value;
              setUrls(newUrls);
            }}
            placeholder={`API URL ${index + 1}`}
            aria-label={`API URL ${index + 1}`}
          />
          {index > 0 && (
            <div className="input-group-append">
              <button
                className="btn btn-danger"
                type="button"
                onClick={() => handleDeleteUrl(index)}
                aria-label="Delete URL">
                &times;
              </button>
            </div>
          )}
        </div>
      ))}
      <button
        className="btn btn-info mb-2"
        type="button"
        onClick={handleAddMoreUrls}
        aria-label="Add more URLs"
      >
        +
      </button>
    </div>
  );
};

export default APIUrlsInput;
