const mongoose = require('mongoose');

const agentSchema = new mongoose.Schema({
    name: { type: String, required: true },
    description: { type: String, required: true },
    readme: { type: String, required: true },
    source: { type: String, required: true },
    skeletonCode: { type: String, required: true },
    additionalResources: { type: String, required: false },
    origin: { type: String, required: true },
    averageRating: { type: Number, default: 0 }, // New field for average rating
    numberOfReviews: { type: Number, default: 0 } // New field for number of reviews
});

module.exports = mongoose.model('Agent', agentSchema);
