import React from 'react';

const Header: React.FC = () => {
  return (
    <div className="text-center mb-4">
      <h1>🦍 Gorilla: API Zoo Data Converter</h1>
      <p className="lead">Easily convert your API data from Option 2 to Option 1 format.</p>
      <div className="text-center mb-4">
        <p>For more information about Option 1 and Option 2 formats, visit <a
          href="https://github.com/ShishirPatil/gorilla/tree/main/data#option-2-url-json"
          target="_blank">this GitHub page</a>.</p>
      </div>
    </div>
  );
};

export default Header;
