import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Card = ({ agent, filter }) => {
  const navigate = useNavigate();
  const [isHovered, setIsHovered] = useState(false);

  const getCardColor = (filter, isHovered) => {
    const filterColors = {
      AI: { normal: '#a8e6cf', hover: '#91d4b7' },           // Mint green
      Data: { normal: '#dcedc1', hover: '#c6d7a8' },         // Light green
      Integration: { normal: '#ffd3b6', hover: '#ffbfa0' },  // Peach
      Communication: { normal: '#ffaaa5', hover: '#ff918f' }, // Soft red
      Database: { normal: '#ff8b94', hover: '#ff6d78' },     // Soft pink
      Finance: { normal: '#a2d5f2', hover: '#8bc3de' },      // Light blue
    };
    const color = filterColors[filter] || { normal: '#f8bbd0', hover: '#e1a2b8' };
    return isHovered ? color.hover : color.normal;
  };

  // Function to render stars based on the rating
  const renderStars = (rating) => {
    let stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} style={{ color: i <= rating ? '#FFD700' : '#e0e0e0' }}>★</span>
      );
    }
    return <div style={{ fontSize: '16px', marginRight: '10px' }}>{stars}</div>;
  };

  // Base style for the card
  const cardStyle = {
    border: '1px solid #e0e0e0',
    borderRadius: '10px',
    padding: '20px',
    cursor: 'pointer',
    boxShadow: isHovered ? '0 10px 20px rgba(0,0,0,0.2)' : '0 5px 15px rgba(0,0,0,0.1)',
    transform: isHovered ? 'translateY(-10px)' : 'none',
    transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    height: '250px', // Fixed height for all cards
    backgroundColor: getCardColor(filter, isHovered)
  };

  const titleStyle = {
    marginBottom: '15px',
    fontSize: '1.4rem',
    fontWeight: '600',
    color: '#007bff',
  };

  const descriptionStyle = {
    fontSize: '1rem',
    color: '#666',
    overflow: 'auto', // Enable scrolling if content overflows
    flexGrow: 1, // Allow the description to grow and take available space
  };

  const ratingStyle = {
    display: 'flex',
    alignItems: 'center',
    marginTop: '10px',
    fontSize: '1rem',
    color: '#333',
  };

  const reviewCountStyle = {
    display: 'flex',
    alignItems: 'center',
    marginLeft: '10px',
  };

  const reviewIconStyle = {
    width: '16px',
    height: '16px',
    marginRight: '5px',
  };

  return (
    <div 
      style={cardStyle} 
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => navigate(`/agents/${agent._id}`)}
    >
      <h3 style={titleStyle}>{agent.name}</h3>
      <p style={descriptionStyle}>{agent.description}</p>
      <div style={ratingStyle}>
        {renderStars(agent.averageRating)}
        <span>{agent.averageRating.toFixed(1)}</span>
        <div style={reviewCountStyle}>
          <span>(</span>
          <img src="user.png" alt="Reviews" style={reviewIconStyle} />
          <span>{agent.numberOfReviews})</span>
        </div>
      </div>
    </div>
  );
};

export default Card;
