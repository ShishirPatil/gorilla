const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const CommentSchema = new Schema({
    content: { type: String, required: true },
    upvotes: { type: Number, default: 0 },
    downvotes: { type: Number, default: 0 },
    createdAt: { type: Date, default: Date.now },
    post: { type: Schema.Types.ObjectId, ref: 'Post' }
});

module.exports = mongoose.model('Comment', CommentSchema);
