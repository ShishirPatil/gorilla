import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Reviews.css'

const Reviews = ({ agentId }) => {
  const [reviews, setReviews] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [reviewsPerPage] = useState(5); // Number of reviews per page

  useEffect(() => {
    fetchReviews();
  }, [agentId]);

  const fetchReviews = async () => {
    try {
      const response = await axios.get(`https://agent-marketplace-2jmb.vercel.app/api/reviews/${agentId}`);
      setReviews(response.data);
    } catch (error) {
      console.error('Failed to fetch reviews', error);
    }
  };

  // Function to render stars based on the rating
  const renderStars = (rating) => {
    let stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} style={{ color: i <= rating ? '#FFD700' : '#e0e0e0' }}>★</span>
      );
    }
    return <div style={{ fontSize: '16px', marginBottom: '5px' }}>{stars}</div>;
  };

  // Review card styling
  const reviewCardStyle = {
    background: '#fff',
    borderRadius: '5px',
    padding: '15px',
    boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
    marginBottom: '20px',
    borderLeft: '5px solid #007BFF'
  };

  // Comment text styling
  const commentStyle = {
    color: '#333',
    fontSize: '14px',
    marginTop: '10px',
    lineHeight: '1.6',
  };

  // Pagination logic
  const indexOfLastReview = currentPage * reviewsPerPage;
  const indexOfFirstReview = indexOfLastReview - reviewsPerPage;
  const currentReviews = reviews.slice(indexOfFirstReview, indexOfLastReview);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  return (
    <div>
      <h3 style={{ marginBottom: '20px' }}>Reviews</h3>
      {currentReviews.length > 0 ? (
        currentReviews.map(review => (
          <div key={review._id} style={reviewCardStyle}>
            {renderStars(review.rating)}
            <p><strong>{review.name}</strong></p>
            <p style={commentStyle}>{review.comment}</p>
          </div>
        ))
      ) : (
        <p>No reviews yet.</p>
      )}
      <Pagination
        reviewsPerPage={reviewsPerPage}
        totalReviews={reviews.length}
        paginate={paginate}
        currentPage={currentPage}
      />
    </div>
  );
};

const Pagination = ({ reviewsPerPage, totalReviews, paginate, currentPage }) => {
  const pageNumbers = [];

  for (let i = 1; i <= Math.ceil(totalReviews / reviewsPerPage); i++) {
    pageNumbers.push(i);
  }

  return (
    <nav>
      <ul className="pagination">
        {pageNumbers.map(number => (
          <li key={number} className={`page-item ${number === currentPage ? 'active' : ''}`}>
            <button onClick={() => paginate(number)} className="page-link">
              {number}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Reviews;
