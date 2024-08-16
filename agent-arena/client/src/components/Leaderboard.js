import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Card } from 'react-bootstrap';
import Select from 'react-select';

// Filter colors for agents based on their categories
const filterColors = {
  AI: { normal: '#a8e6cf', hover: '#91d4b7' },
  Data: { normal: '#dcedc1', hover: '#c6d7a8' },
  Integration: { normal: '#ffd3b6', hover: '#ffbfa0' },
  Communication: { normal: '#ffaaa5', hover: '#ff918f' },
  Database: { normal: '#ff8b94', hover: '#ff6d78' },
  Finance: { normal: '#a2d5f2', hover: '#8bc3de' },
  Search: { normal: '#c5cae9', hover: '#9fa8da' },
  Automation: { normal: '#ffccbc', hover: '#ffab91' },
  Research: { normal: '#ffe0b2', hover: '#ffcc80' },
  Analytics: { normal: '#f8bbd0', hover: '#e1a2b8' },
};

// Framework-specific colors with hover states
const frameworkColors = {
  langchain: { normal: '#a3e4d7', hover: '#76d7c4' },
  llamaindex: { normal: '#d1f2eb', hover: '#b2e4d5' },
  composio: { normal: '#f5cba7', hover: '#f4b184' },
  crewai: { normal: '#f9e79f', hover: '#f7dc6f' },
  'openai assistants': { normal: '#a9cce3', hover: '#87bdd8' },
  'anthropic tool use': { normal: '#f7cac9', hover: '#f4b0a9' },
};

// Adjusted model-specific colors for GPT and Claude
const modelColors = {
  gpt: { normal: '#9bc2c4', hover: '#76c776' },  // More desaturated green
  claude: { normal: '#ffbfa0', hover: '#ff7f50' },  // Adjusted orange
};

// Unified tool color with hover state
const toolColor = { normal: '#87ceeb', hover: '#6495ed' };  // Light Blue for Tools

const categoryOptions = Object.keys(filterColors).map(cat => ({
  value: cat,
  label: (
    <span>
      <span
        style={{
          display: 'inline-block',
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          backgroundColor: filterColors[cat].normal,
          marginRight: '8px',
        }}
      ></span>
      {cat}
    </span>
  ),
}));

const metricOptions = [
  { value: 'skill', label: 'Skill Parameter' },
  { value: 'pass', label: 'Pass Count' },
  { value: 'fail', label: 'Fail Count' },
  { value: 'executionTime', label: 'Execution Time' },
  { value: 'votes', label: 'Total Votes' },
  { value: 'name', label: 'Alphabetical' },
];

const customStyles = {
  control: (base) => ({
    ...base,
    minHeight: 40,
    fontSize: 14,
  }),
  menu: (base) => ({
    ...base,
    fontSize: 14,
  }),
  singleValue: (base) => ({
    ...base,
    color: '#4b0082',
  }),
  option: (base, { isFocused }) => ({
    ...base,
    color: '#4b0082',
    backgroundColor: isFocused ? '#d3d3d3' : 'white',
  }),
};

const LeaderboardTable = ({ title, data, sortBy }) => {
  const tableStyles = {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: '#1e272e',
    color: '#4b0082',
  };

  const thStyles = {
    backgroundColor: '#34495e',
    color: '#ffffff',
    padding: '12px',
    textAlign: 'center',
    borderBottom: '2px solid #2c3e50',
  };

  const tdStyles = {
    padding: '12px',
    textAlign: 'center',
    borderBottom: '1px solid #34495e',
  };

  return (
    <Card className="p-3 mb-4 shadow-sm" style={{ backgroundColor: '#2c3e50', borderRadius: '8px' }}>
      <h3 className="text-center" style={{ color: '#ffffff' }}>{title}</h3>
      <div style={{ maxHeight: '400px', overflowY: data.length > 10 ? 'scroll' : 'auto' }}>  {/* Set max height and enable scroll */}
        <table style={tableStyles}>
          <thead>
            <tr>
              <th style={thStyles}>#</th> {/* Numbering header */}
              <th style={{ ...thStyles, textAlign: 'left' }}>Name</th>
              <th style={thStyles}>Skill Parameter</th>
              <th style={thStyles}>Total Votes</th>
              {sortBy === 'agents' && <>
                <th style={thStyles}>Average Time (s)</th>
                <th style={thStyles}>Success</th>
                <th style={thStyles}>Failure</th>
              </>}
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {  // Display only the top 10 items
              let backgroundColor = '#2c3e50'; // Default background color
              let hoverColor = '#34495e'; // Default hover color

              if (sortBy === 'agents') {
                backgroundColor = filterColors[item.category]?.normal || backgroundColor;
                hoverColor = filterColors[item.category]?.hover || hoverColor;
              } else if (sortBy === 'models') {
                const modelType = item.name.startsWith('claude') ? 'claude' : 'gpt';
                backgroundColor = modelColors[modelType]?.normal || backgroundColor;
                hoverColor = modelColors[modelType]?.hover || hoverColor;
              } else if (sortBy === 'tools') {
                backgroundColor = toolColor.normal;
                hoverColor = toolColor.hover;
              } else if (sortBy === 'frameworks') {
                backgroundColor = frameworkColors[item.name.toLowerCase()]?.normal || backgroundColor;
                hoverColor = frameworkColors[item.name.toLowerCase()]?.hover || hoverColor;
              }

              return (
                <tr
                  key={index}
                  style={{ backgroundColor }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverColor}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = backgroundColor}
                >
                  <td style={tdStyles}>{index + 1}</td> {/* Numbering each row */}
                  <td style={{ ...tdStyles, textAlign: 'left' }}>{item.name}</td>
                  <td style={tdStyles}>{item.skillParameter.toFixed(2)}</td>
                  <td style={tdStyles}>{item.totalVotes}</td>
                  {sortBy === 'agents' && <>
                    <td style={tdStyles}>{item.averageExecutionTime.toFixed(2)}</td>
                    <td style={tdStyles}>{item.passCount}</td>
                    <td style={tdStyles}>{item.failCount}</td>
                  </>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};


const Leaderboard = () => {
  const [agents, setAgents] = useState([]);
  const [models, setModels] = useState([]);
  const [tools, setTools] = useState([]);
  const [frameworks, setFrameworks] = useState([]);
  const [category, setCategory] = useState('Search'); // Set default to 'Search'
  const [sortBy, setSortBy] = useState('skill');

  useEffect(() => {
    const fetchData = async () => {
      const agentsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard?category=${category}&sortBy=${sortBy}`);
      const modelsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/models?category=${category}&sortBy=${sortBy}`);
      const toolsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/tools?category=${category}&sortBy=${sortBy}`);
      const frameworksResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/frameworks?category=${category}&sortBy=${sortBy}`);
      setAgents(agentsResponse.data);
      setModels(modelsResponse.data);
      setTools(toolsResponse.data);
      setFrameworks(frameworksResponse.data);
    };

    fetchData();
  }, [category, sortBy]);

  const handleCategoryChange = (selectedOption) => {
    setCategory(selectedOption ? selectedOption.value : '');
  };

  const handleSortByChange = (selectedOption) => {
    setSortBy(selectedOption ? selectedOption.value : 'skill');
  };

  return (
    <Container fluid>
      <h1 className="text-center my-4" style={{ color: '#ffffff' }}>Agent Leaderboard</h1>
      <div className="d-flex justify-content-between mb-3 flex-column flex-md-row align-items-start align-items-md-stretch">
        <div className="dropdown-container mb-3 mb-md-0">
          <label htmlFor="category-select" style={{ color: '#ffffff', marginBottom: '5px', display: 'block' }}>Select Category</label>
          <Select
            id="category-select"
            options={categoryOptions}
            onChange={handleCategoryChange}
            isClearable
            placeholder="Select Category"
            styles={customStyles}
            defaultValue={categoryOptions.find(option => option.value === 'Search')} // Set initial selected option to 'Search'
          />
        </div>
        <div className="dropdown-container">
          <label htmlFor="metric-select" style={{ color: '#ffffff', marginBottom: '5px', display: 'block' }}>Select Metric</label>
          <Select
            id="metric-select"
            options={metricOptions}
            onChange={handleSortByChange}
            defaultValue={metricOptions[0]}
            styles={customStyles}
          />
        </div>
      </div>

      {/* Agents Leaderboard */}
      <LeaderboardTable title="Agents Leaderboard" data={agents} sortBy="agents" />

      {/* Models and Tools Leaderboards Side by Side */}
      <div className="d-flex justify-content-between">
        <div style={{ width: '48%' }}>
          <LeaderboardTable title="Models Leaderboard" data={models} sortBy="models" />
        </div>
        <div style={{ width: '48%' }}>
          <LeaderboardTable title="Tools Leaderboard" data={tools} sortBy="tools" />
        </div>
      </div>

      {/* Frameworks Leaderboard */}
      <LeaderboardTable title="Frameworks Leaderboard" data={frameworks} sortBy="frameworks" />
    
    <style jsx>{`
      .dropdown-container {
        width: 100%;
      }
      @media (min-width: 768px) {
        .dropdown-container {
          width: 48%;
        }
      }
    `}</style>
  </Container>
);
};

export default Leaderboard;
