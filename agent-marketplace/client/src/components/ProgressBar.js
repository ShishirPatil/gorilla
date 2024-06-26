import React from 'react';
import './ProgressBar.css';

const ProgressBar = ({ runningAgents, totalAgents }) => {
  const progressPercentage = (runningAgents / totalAgents) * 100;

  return (
    <div className="progress-bar-container">
      <div className="progress-bar">
        <div className="progress" style={{ width: `${progressPercentage}%` }}></div>
      </div>
      <div className="progress-info">
        <span>{runningAgents} / {totalAgents} agents are passing all checks</span>
      </div>
    </div>
  );
};

export default ProgressBar;
