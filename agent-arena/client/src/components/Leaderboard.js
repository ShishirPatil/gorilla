import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Container, Card } from 'react-bootstrap';
import Select from 'react-select';
import { Analytics } from "@vercel/analytics/react";
import { ThemeContext } from "../App";


// Filter colors for agents based on their categories
const agentFilterColors = {
  AI: { normal: '#a8e6cf', hover: '#91d4b7' },
  Data: { normal: '#dcedc1', hover: '#c6d7a8' },
  Integration: { normal: '#ffd3b6', hover: '#ffbfa0' },
  Communication: { normal: '#ffaaa5', hover: '#ff918f' },
  Database: { normal: '#ff8b94', hover: '#ff6d78' },
  Finance: { normal: '#a2d5f2', hover: '#8bc3de' },
  Search: { normal: '#c5cae9', hover: '#9fa8da' },
  Automation: { normal: '#ffccbc', hover: '#ffab91' },
  Research: { normal: '#ffe0b2', hover: '#ffcc80' },
};

// Filter colors for tools based on their categories
const toolFilterColors = {
  Automation: { normal: '#ffccbc', hover: '#ffab91' },
  Communication: { normal: '#ffaaa5', hover: '#ff918f' },
  Data: { normal: '#dcedc1', hover: '#c6d7a8' },
  Database: { normal: '#ff8b94', hover: '#ff6d78' },
  Finance: { normal: '#a2d5f2', hover: '#8bc3de' },
  General: { normal: '#ffccbc', hover: '#ffab91' },  // General category
  Integration: { normal: '#ffd3b6', hover: '#ffbfa0' },
  Research: { normal: '#ffe0b2', hover: '#ffcc80' },
  Search: { normal: '#c5cae9', hover: '#9fa8da' },
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

// Adjusted model-specific colors
const modelColors = {
  OpenAI: { normal: '#9bc2c4', hover: '#76c776' },  // OpenAI (gpt)
  Anthropic: { normal: '#ffbfa0', hover: '#ff7f50' },  // Anthropic (claude)
  Perplexity: { normal: '#A9A9A9', hover: '#808080' },  // Perplexity (sonar)
  'Mistral AI': { normal: '#FFA500', hover: '#FF8C00' },  // Mistral (mistral)
  Google: { normal: '#4285F4', hover: '#357ae8' },  // Google (gemini)
  Meta: { normal: '#4267B2', hover: '#365899' },  // Meta (llama)
};

// Provider options for filtering models by provider with colors in the dropdown
const providerOptions = Object.keys(modelColors).map(provider => ({
  value: provider,
  label: (
    <span>
      <span
        style={{
          display: 'inline-block',
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          backgroundColor: modelColors[provider].normal,
          marginRight: '8px',
        }}
      ></span>
      {provider}
    </span>
  ),
}));

const agentCategoryOptions = Object.keys(agentFilterColors).map(cat => ({
  value: cat,
  label: (
    <span>
      <span
        style={{
          display: 'inline-block',
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          backgroundColor: agentFilterColors[cat].normal,
          marginRight: '8px',
        }}
      ></span>
      {cat}
    </span>
  ),
}));

const toolCategoryOptions = Object.keys(toolFilterColors).map(cat => ({
  value: cat,
  label: (
    <span>
      <span
        style={{
          display: 'inline-block',
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          backgroundColor: toolFilterColors[cat].normal,
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
      <div style={{ maxHeight: '400px', overflowY: data.length > 10 ? 'scroll' : 'auto' }}>
        <table style={tableStyles}>
          <thead>
            <tr>
              <th style={thStyles}>#</th>
              <th style={{ ...thStyles, textAlign: 'left' }}>Name</th>
              <th style={thStyles}>Skill Parameter</th>
              <th style={thStyles}>Vote %</th>
              {sortBy === 'agents' && <>
                <th style={thStyles}>Average Time (s)</th>
                <th style={thStyles}>Success Rate</th>
              </>}
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              let backgroundColor = '#2c3e50';
              let hoverColor = '#34495e';

              if (sortBy === 'agents') {
                backgroundColor = agentFilterColors[item.category]?.normal || backgroundColor;
                hoverColor = agentFilterColors[item.category]?.hover || hoverColor;
              } else if (sortBy === 'tools') {
                backgroundColor = toolFilterColors[item.category]?.normal || backgroundColor;
                hoverColor = toolFilterColors[item.category]?.hover || hoverColor;
              } else if (sortBy === 'models') {
                backgroundColor = modelColors[item.provider]?.normal || backgroundColor;
                hoverColor = modelColors[item.provider]?.hover || hoverColor;
              } else if (sortBy === 'frameworks') {
                backgroundColor = frameworkColors[item.name.toLowerCase()]?.normal || backgroundColor;
                hoverColor = frameworkColors[item.name.toLowerCase()]?.hover || hoverColor;
              }

              const successRate = item.passCount + item.failCount > 0
                ? ((item.passCount / (item.passCount + item.failCount))).toFixed(2)
                : 'N/A';

              return (
                <tr
                  key={index}
                  style={{ backgroundColor }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverColor}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = backgroundColor}
                >
                  <td style={tdStyles}>{index + 1}</td>
                  <td style={{ ...tdStyles, textAlign: 'left' }}>{item.name}</td>
                  <td style={tdStyles}>{item.skillParameter.toFixed(2)}</td>
                  <td style={tdStyles}>{item.votePercentage}</td> {/* Display vote percentage */}
                  {sortBy === 'agents' && <>
                    <td style={tdStyles}>{item.averageExecutionTime.toFixed(2)}</td>
                    <td style={tdStyles}>{successRate}</td>
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
  const [category, setCategory] = useState('Finance'); // Default category
  const [toolCategory, setToolCategory] = useState('Search'); // Tool category
  const [provider, setProvider] = useState(''); // Provider filter
  const [sortBy, setSortBy] = useState('skill'); // Sort by field
  const { theme } = useContext(ThemeContext);


  useEffect(() => {
    const fetchData = async () => {
      const agentsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard?category=${category}&sortBy=${sortBy}`);
      const modelsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/models?sortBy=${sortBy}&provider=${provider}`);
      const toolsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/tools?category=${toolCategory}&sortBy=${sortBy}`);
      const frameworksResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/frameworks?category=${category}&sortBy=${sortBy}`);
      setAgents(agentsResponse.data);
      setModels(modelsResponse.data);
      setTools(toolsResponse.data);
      setFrameworks(frameworksResponse.data);
    };

    fetchData();
  }, [category, toolCategory, provider, sortBy]);

  const handleCategoryChange = (selectedOption) => {
    setCategory(selectedOption ? selectedOption.value : '');
  };

  const handleToolCategoryChange = (selectedOption) => {
    setToolCategory(selectedOption ? selectedOption.value : '');
  };

  const handleProviderChange = (selectedOption) => {
    setProvider(selectedOption ? selectedOption.value : '');
  };

  const handleSortByChange = (selectedOption) => {
    setSortBy(selectedOption ? selectedOption.value : 'skill');
  };

  return (
    <Container fluid>
      <h1 className="text-center my-4" style={{ color: '#ffffff' }}>Leaderboard</h1>
      <p className="text-center mb-4" style={{color: theme === "light" ? "#000" : "#ffffff"}}>
        The Leaderboard ranks AI agents, models, tools, and frameworks using ELO-style ratings from battles. 
        It offers insights into agent capabilities across various categories and leverages battle data to evaluate individual agent components, 
        providing a comprehensive view of agent performance in different domains.
      </p>
      {/* Tools and Models Leaderboards Side by Side */}
      <div className="leaderboard-container mb-4">
        <div className="leaderboard-item">
          <div className="mb-3">
            <label htmlFor="provider-select" style={{ color: theme === "light" ? "#000" : "#ffffff", marginBottom: '5px', display: 'block' }}>Select Provider</label>
            <Select
              id="provider-select"
              options={providerOptions}
              onChange={handleProviderChange}
              isClearable
              placeholder="Sort by Provider"
              styles={customStyles}
            />
          </div>
          <LeaderboardTable
            title={`Models Leaderboard${provider ? ` (${provider})` : ''}`}
            data={models}
            sortBy="models"
          />
        </div>
        <div className="leaderboard-item">
          <div className="mb-3">
            <label htmlFor="tool-category-select" style={{ color: theme === "light" ? "#000" : "#ffffff", marginBottom: '5px', display: 'block' }}>Select Tool Category</label>
            <Select
              id="tool-category-select"
              options={toolCategoryOptions}
              onChange={handleToolCategoryChange}
              isClearable
              placeholder="Select Tool Category"
              styles={customStyles}
              defaultValue={toolCategoryOptions.find(option => option.value === 'Search')}
            />
          </div>
          <LeaderboardTable
              title={`Tools Leaderboard${toolCategory ? ` (${toolCategory})` : ''}`}
              data={tools}
              sortBy="tools"
            />
        </div>
      </div>

      {/* Frameworks Leaderboard */}
      <LeaderboardTable title="Frameworks Leaderboard" data={frameworks} sortBy="frameworks" />

      {/* Dropdowns for Agents Leaderboard */}
      <div className="d-flex justify-content-between mb-3 flex-column flex-md-row align-items-start align-items-md-stretch">
        <div className="dropdown-container mb-3 mb-md-0">
          <label htmlFor="category-select" style={{ color: theme === "light" ? "#000" : "#ffffff", marginBottom: '5px', display: 'block' }}>Select Agent Category</label>
          <Select
            id="category-select"
            options={agentCategoryOptions}
            onChange={handleCategoryChange}
            isClearable
            placeholder="Select Category"
            styles={customStyles}
            defaultValue={agentCategoryOptions.find(option => option.value === 'Finance')}
          />
        </div>
        <div className="dropdown-container">
          <label htmlFor="metric-select" style={{ color: theme === "light" ? "#000" : "#ffffff", marginBottom: '5px', display: 'block' }}>Sort by Metric</label>
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
      <LeaderboardTable
        title={`Agents Leaderboard${category ? ` (${category})` : ''}`}
        data={agents}
        sortBy="agents"
      />
      <style jsx>{`
        .dropdown-container {
          width: 100%;
        }

        @media (min-width: 768px) {
          .dropdown-container {
            width: 48%;
          }
        }

        .leaderboard-container {
          display: flex;
          flex-direction: column;
        }

        @media (min-width: 768px) {
          .leaderboard-container {
            flex-direction: row;
            justify-content: space-between;
          }

          .leaderboard-item {
            width: 48%;
          }
        }
      `}</style>
    </Container>
  );
};

export default Leaderboard;
