import React from 'react';

const Header: React.FC = () => {
  return (
    <div className="text-center mb-4">
      <h1>🦍 Gorilla: API Zoo Data Converter</h1>
      <div className="text-center">
        <p className="lead">Easily add your API information to Gorilla API Store</p>
        <p>For more information about Gorilla API Store, visit <a
          href="https://github.com/ShishirPatil/gorilla/tree/main/data#gorilla-api-store"
          target="_blank">this GitHub page</a>.</p>
      </div>
    </div>
  );
};

export default Header;
