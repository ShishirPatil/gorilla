import React, { useContext } from 'react';
import Select from 'react-select';
import { ThemeContext } from '../App'; // Assuming you have a ThemeContext in your App

const AgentDropdown = ({ agents, selectedAgent, onSelect }) => {
  const { theme } = useContext(ThemeContext);

  const options = agents.map(agent => ({
    value: agent._id,
    label: agent.name,
  }));

  const handleSelect = (selectedOption) => {
    const agent = agents.find(agent => agent._id === selectedOption.value);
    onSelect(agent);
  };

  const customStyles = {
    control: (provided) => ({
      ...provided,
      backgroundColor: theme === 'dark' ? '#1e1e2f' : '#fff', // Dark for dark mode, white for light mode
      borderColor: theme === 'dark' ? '#8a2be2' : '#2966ff', // Purple border for dark mode, gray for light mode
      color: theme === 'dark' ? '#fff' : '#000', // White text for dark mode, black for light mode
      minHeight: '40px',
      height: '40px',
      boxShadow: 'none',
      '&:hover': {
        borderColor: theme === 'dark' ? '#8a2be2' : '#888', // Hover color based on theme
      },
    }),
    menu: (provided) => ({
      ...provided,
      backgroundColor: theme === 'dark' ? '#1e1e2f' : '#fff', // Match background color to the control
      color: theme === 'dark' ? '#fff' : '#000', // Text color based on theme
      zIndex: 9999, // Ensure it appears on top of other elements
    }),
    menuPortal: (provided) => ({
      ...provided,
      zIndex: 9999, // Ensure the portal is above other elements
    }),
    singleValue: (provided) => ({
      ...provided,
      color: theme === 'dark' ? '#fff' : '#000', // Text color for selected value
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected
        ? theme === 'dark' ? '#8a2be2' : '#ddd' // Selected option background color based on theme
        : theme === 'dark' ? '#1e1e2f' : '#fff', // Normal option background color based on theme
      color: theme === 'dark' ? '#fff' : '#000', // Text color based on theme
      '&:hover': {
        backgroundColor: theme === 'dark' ? '#8a2be2' : '#eee', // Hover background color based on theme
      },
    }),
    dropdownIndicator: (provided) => ({
      ...provided,
      color: theme === 'dark' ? '#fff' : '#000', // Color of the dropdown arrow
    }),
    indicatorSeparator: () => ({
      display: 'none', // Remove the separator for a cleaner look
    }),
    input: (provided) => ({
      ...provided,
      color: theme === 'dark' ? '#ccc' : '#000', // Lighter text color for dark mode
    }),
  };

  return (
    <Select
      value={selectedAgent ? { value: selectedAgent._id, label: selectedAgent.name } : null}
      onChange={handleSelect}
      options={options}
      placeholder="Select Agent"
      isSearchable
      styles={customStyles}
      classNamePrefix="react-select"
      menuPortalTarget={document.body} // Render the dropdown as a portal to avoid being clipped
      menuPosition="fixed" // Position the menu absolutely relative to the viewport
    />
  );
};

export default AgentDropdown;
