import React from 'react';
import './StaticFileInput.css'; // Create and import this CSS file for styling

const StaticFileInput = ({ filename }) => (
  <div className="custom-file">
    <input type="file" className="custom-file-input" disabled style={{ display: 'none' }} />
    <label className="custom-file-label static-file-label">{filename}</label>
  </div>
);

export default StaticFileInput;
