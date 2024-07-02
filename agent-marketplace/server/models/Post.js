const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const PostSchema = new Schema({
    title: { type: String, required: true },
    content: { type: String, required: true },
    comments: [{ type: Schema.Types.ObjectId, ref: 'Comment' }],
    upvotes: { type: Number, default: 0 },
    downvotes: { type: Number, default: 0 },
    createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Post', PostSchema);
