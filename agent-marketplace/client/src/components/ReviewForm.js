import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import UserContext from '../UserContext';
import StarRatingComponent from 'react-star-rating-component';

const ReviewForm = ({ agentId }) => {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const { user } = useContext(UserContext);
  const [name, setName] = useState(user ? user.name : '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFeedbackMessage('');

    const payload = { agentId, name, rating, comment };

    try {
      await axios.post('https://agent-marketplace-2jmb.vercel.app/api/reviews', payload);
      setFeedbackMessage('Review submitted successfully');
      setRating(5);
      setComment('');
      if (!user) setName('');  // Only reset name if the user is not logged in
      window.location.reload();
    } catch (error) {
      console.error('Failed to submit review', error);
      setFeedbackMessage('Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isNameRequired = !user && comment.trim().length > 0;

  // Form and components styling
  const formStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    marginTop: '20px',
  };

  const inputStyle = {
    padding: '10px',
    borderRadius: '5px',
    border: '1px solid #ddd',
    fontSize: '16px',
  };

  const buttonStyle = {
    padding: '10px 15px',
    border: 'none',
    borderRadius: '5px',
    background: '#007bff',
    color: 'white',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
    marginTop: '10px',
  };

  const infoStyle = {
    fontSize: '12px',
    color: '#666',
  };

  return (
    <div>
      <form onSubmit={handleSubmit} style={formStyle}>
        {!user && (
          <div>
            <label>
              Name:{isNameRequired && <span style={{ color: 'red' }}>*</span>}
              <span style={infoStyle}>(Required if commenting)</span>
            </label>
            <input 
              type="text" 
              value={name} 
              onChange={e => setName(e.target.value)} 
              style={inputStyle} 
              required={isNameRequired}
            />
          </div>
        )}
        <div>
          <label>Rating: </label>
          <StarRatingComponent 
            name="rating" 
            starCount={5} 
            value={rating} 
            onStarClick={(nextValue) => setRating(nextValue)} 
          />
        </div>
        <div>
          <label>Comment:</label>
          <textarea 
            value={comment} 
            onChange={e => setComment(e.target.value)}
            style={{...inputStyle, height: '100px'}} 
          ></textarea>
        </div>
        <button type="submit" style={buttonStyle} disabled={isSubmitting}>Submit Review</button>
      </form>
      {feedbackMessage && <div>{feedbackMessage}</div>}
    </div>
  );
};

export default ReviewForm;
