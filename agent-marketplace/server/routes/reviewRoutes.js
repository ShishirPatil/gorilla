const express = require('express');
const Review = require('../models/Review'); 
const Agent = require('../models/Agent'); // Import the Agent model
const router = express.Router();

// Post a review
router.post('/', async (req, res) => {
  try {
    const review = new Review(req.body); 
    await review.save();

    // Find the agent and update its average rating and number of reviews
    const agent = await Agent.findById(review.agentId);
    const reviews = await Review.find({ agentId: review.agentId });

    const numberOfReviews = reviews.length;
    const averageRating = reviews.reduce((acc, cur) => acc + cur.rating, 0) / numberOfReviews;

    agent.numberOfReviews = numberOfReviews;
    agent.averageRating = averageRating;
    await agent.save();

    res.status(201).json(review);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

// Get all reviews for a specific agent
router.get('/:agentId', async (req, res) => {
  try {
    const reviews = await Review.find({ agentId: req.params.agentId });
    res.json(reviews);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;
