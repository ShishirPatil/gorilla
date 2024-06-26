import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Card = ({ agent }) => {
  const navigate = useNavigate();
  const [isHovered, setIsHovered] = useState(false);

  const getPastelColor = () => {
    const pastelColors = [
      '#a8e6cf', // Mint green
      '#dcedc1', // Light green
      '#ffd3b6', // Peach
      '#ffaaa5', // Soft red
      '#ff8b94', // Soft pink
      '#a2d5f2', // Light blue
    ];
    return pastelColors[Math.floor(Math.random() * pastelColors.length)];
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
    transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    height: '250px', // Fixed height for all cards
    backgroundColor: getPastelColor(),
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
