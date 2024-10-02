import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Container, Card } from 'react-bootstrap';
import Select from 'react-select';
import { Analytics } from "@vercel/analytics/react";
import { ThemeContext } from "../App";

// Filter colors for tools and agents based on their categories
const toolFilterColors = {
  'Search Engines': { normal: '#c5cae9', hover: '#9fa8da' },
  'Simple Math': { normal: '#ffd3b6', hover: '#ffbfa0' },
  'Knowledge Bases': { normal: '#ffe0b2', hover: '#ffcc80' },
  'Math/CS Academic Search': { normal: '#ffccbc', hover: '#ffab91' },
  'Code Interpreter': { normal: '#a9cce3', hover: '#87bdd8' },
};

const agentFilterColors = {
  'Search Engines': { normal: '#c5cae9', hover: '#9fa8da' },
  'Simple Math': { normal: '#ffd3b6', hover: '#ffbfa0' },
  'Knowledge Bases': { normal: '#ffe0b2', hover: '#ffcc80' },
  'Math/CS Academic Search': { normal: '#ffccbc', hover: '#ffab91' },
  'Code Interpreter': { normal: '#a9cce3', hover: '#87bdd8' },
};

// Tools (and agents) to include in the leaderboard
const validToolNames = [
  'google-serper', 'you-search', 'tavily-search', 'exa-search', 'brave-search',
  'llamaindex-code-interpreter', 'openai-code-interpreter', 'riza-code-interpreter', 'python-repl',
  'wolfram-alpha', 'calculator', 'wikipedia', 'asknews', 'arxiv'
];

// Framework-specific colors with hover states
const frameworkColors = {
  langchain: { normal: '#a3e4d7', hover: '#76d7c4' },
  llamaindex: { normal: '#d1f2eb', hover: '#b2e4d5' },
  composio: { normal: '#f5cba7', hover: '#f4b184' },
  crewai: { normal: '#f9e79f', hover: '#f7dc6f' },
  'openai assistants': { normal: '#a9cce3', hover: '#87bdd8' },
  'anthropic tool use': { normal: '#f7cac9', hover: '#f4b0a9' }
};

// Adjusted model-specific colors
const modelColors = {
  OpenAI: { normal: '#9bc2c4', hover: '#76c776' },
  Anthropic: { normal: '#ffbfa0', hover: '#ff7f50' },
  Perplexity: { normal: '#A9A9A9', hover: '#808080' },
  'Mistral AI': { normal: '#FFA500', hover: '#FF8C00' },
  Google: { normal: '#4285F4', hover: '#357ae8' },
  Meta: { normal: '#4267B2', hover: '#365899' }
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
          marginRight: '8px'
        }}
      ></span>
      {provider}
    </span>
  )
}));

// Tool category options based on toolFilterColors
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
          marginRight: '8px'
        }}
      ></span>
      {cat}
    </span>
  )
}));

const metricOptions = [
  { value: 'skillParameter', label: 'Skill Parameter' },
  { value: 'pass', label: 'Pass Count' },
  { value: 'fail', label: 'Fail Count' },
  { value: 'executionTime', label: 'Execution Time' },
  { value: 'votes', label: 'Total Votes' },
  { value: 'name', label: 'Alphabetical' }
];

const customStyles = {
  control: (base) => ({
    ...base,
    minHeight: 40,
    fontSize: 14
  }),
  menu: (base) => ({
    ...base,
    fontSize: 14
  }),
  singleValue: (base) => ({
    ...base,
    color: '#4b0082'
  }),
  option: (base, { isFocused }) => ({
    ...base,
    color: '#4b0082',
    backgroundColor: isFocused ? '#d3d3d3' : 'white'
  })
};

const parseAgentData = (fileContent) => {
  const categories = ['Search Engines', 'Simple Math', 'Knowledge Bases', 'Math/CS Academic Search', 'Code Interpreter'];
  const parsedData = {};
  const allAgentNames = new Set();

  categories.forEach(category => {
    parsedData[category] = {};
  });

  let currentCategory = '';
  const lines = fileContent.split('\n');

  lines.forEach(line => {
    categories.forEach(category => {
      if (line.includes(`ELO Ratings for ${category} category`)) {
        currentCategory = category;
      }
    });

    const match = line.match(/(.+):\s+(\d+\.\d+)/);
    if (match && currentCategory) {
      const agentName = match[1].trim();
      const eloRating = parseFloat(match[2].trim());
      parsedData[currentCategory][agentName] = eloRating;
      allAgentNames.add(agentName);
    }
  });

  return { parsedData, allAgentNames };
};

const LeaderboardTable = ({ title, data, sortBy, selectedCategory }) => {
  const tableStyles = {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: '#1e272e',
    color: '#4b0082'
  };

  const thStyles = {
    backgroundColor: '#34495e',
    color: '#ffffff',
    padding: '12px',
    textAlign: 'center',
    borderBottom: '2px solid #2c3e50'
  };

  const tdStyles = {
    padding: '12px',
    textAlign: 'center',
    borderBottom: '1px solid #34495e'
  };

  const getAgentColor = (categories) => {
    if (!Array.isArray(categories)) {
      return agentFilterColors[categories] || { normal: '#2c3e50', hover: '#34495e' };
    }

    for (let category of categories) {
      if (agentFilterColors[category]) {
        return agentFilterColors[category];
      }
    }

    return { normal: '#2c3e50', hover: '#34495e' };
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
                const colors = getAgentColor(item.category);
                backgroundColor = colors.normal;
                hoverColor = colors.hover;
              } else if (sortBy === 'tools') {
                const categoryToUse = Array.isArray(item.category) 
                  ? (selectedCategory && item.category.includes(selectedCategory) 
                      ? selectedCategory 
                      : item.category[0])
                  : item.category;
                backgroundColor = toolFilterColors[categoryToUse]?.normal || backgroundColor;
                hoverColor = toolFilterColors[categoryToUse]?.hover || hoverColor;
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
                  <td style={tdStyles}>{item.votePercentage}</td>
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
// Main Leaderboard Component

const Leaderboard = () => {
  const sortData = (data, sortField) => {
    return [...data].sort((a, b) => {
      if (sortField === 'name') {
        return a.name.localeCompare(b.name);
      } else {
        return b[sortField] - a[sortField];
      }
    });
  };

  const [agents, setAgents] = useState([]);
  const [models, setModels] = useState([]);
  const [tools, setTools] = useState([]);
  const [frameworks, setFrameworks] = useState([]);
  const [category, setCategory] = useState('Search Engines'); // Default agent category
  const [toolCategory, setToolCategory] = useState('Code Interpreter'); // Default tool category
  const [provider, setProvider] = useState(''); // Provider filter
  const [agentSortBy, setAgentSortBy] = useState('skillParameter'); // Sort by field for agents
  const [toolSortBy] = useState('skill'); // Sort by field for tools
  const { theme } = useContext(ThemeContext);
  const [rawAgentData, setRawAgentData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const encodedToolCategory = encodeURIComponent(toolCategory);
        const encodedCategory = encodeURIComponent(category);
        const fileResponse = await fetch('/elo_ratings_by_category.txt');
        const fileContent = await fileResponse.text();
        const { parsedData, allAgentNames } = parseAgentData(fileContent);

        const agentsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard?category=${encodedCategory}&sortBy=${agentSortBy}`);
        const toolsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/tools?category=${encodedToolCategory}&sortBy=${toolSortBy}`);
        const modelsResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/models?sortBy=${toolSortBy}&provider=${provider}`);
        const frameworksResponse = await axios.get(`https://agent-arena.vercel.app/api/leaderboard/frameworks`);

        const filteredAgents = agentsResponse.data
          .filter(agent => allAgentNames.has(agent.name))
          .map(agent => ({
            ...agent,
            skillParameter: parsedData[category][agent.name] || agent.skillParameter
          }));

        setRawAgentData(filteredAgents);
        setAgents(sortData(filteredAgents, agentSortBy));

        const toolsData = toolsResponse.data.filter(tool => validToolNames.includes(tool.name));
        const sortedTools = sortData(toolsData, toolSortBy);
        setTools(sortedTools);

        setModels(modelsResponse.data);
        setFrameworks(frameworksResponse.data);
      } catch (error) {
        console.error("Error fetching leaderboard data:", error);
      }
    };

    fetchData();
  }, [category, toolCategory, provider, agentSortBy]);

  useEffect(() => {
    setAgents(sortData(rawAgentData, agentSortBy));
  }, [agentSortBy, rawAgentData]);

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
    setAgentSortBy(selectedOption ? selectedOption.value : 'skillParameter');
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
              defaultValue={toolCategoryOptions.find(option => option.value === 'Code Interpreter')}
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
            options={toolCategoryOptions}
            onChange={handleCategoryChange}
            isClearable
            placeholder="Select Category"
            styles={customStyles}
            defaultValue={toolCategoryOptions.find(option => option.value === 'Search Engines')}
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

      <LeaderboardTable
        title={`Agents Leaderboard${category ? ` (${category})` : ''}`}
        data={agents}
        sortBy="agents"
        selectedCategory={category}
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