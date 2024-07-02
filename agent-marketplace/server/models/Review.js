const mongoose = require('mongoose');

const reviewSchema = new mongoose.Schema({
  agentId: { type: mongoose.Schema.Types.ObjectId, ref: 'Agent', required: true },
  name: { type: String, required: function() { return this.comment && this.comment.length > 0; } },
  rating: { type: Number, required: true, min: 1, max: 5 },
  comment: { type: String, required: false },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Review', reviewSchema);
