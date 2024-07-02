const express = require('express');
const router = express.Router();
const Post = require('../models/Post');
const Comment = require('../models/Comment');

// Get all posts
router.get('/posts', async (req, res) => {
    try {
        const posts = await Post.find().populate('comments').exec();
        res.json(posts);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

router.get('/posts/:postId', async (req, res) => {
    try {
        const post = await Post.findById(req.params.postId).populate('comments');
        res.json(post);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

// Create a new post
router.post('/posts', async (req, res) => {
    const post = new Post({
        title: req.body.title,
        content: req.body.content
    });

    try {
        const newPost = await post.save();
        res.status(201).json(newPost);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Upvote a post
router.post('/posts/:postId/upvote', async (req, res) => {
    try {
        const post = await Post.findById(req.params.postId);
        post.upvotes += 1;
        await post.save();
        res.json(post);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Downvote a post
router.post('/posts/:postId/downvote', async (req, res) => {
    try {
        const post = await Post.findById(req.params.postId);
        post.downvotes += 1;
        await post.save();
        res.json(post);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Add a comment to a post
router.post('/posts/:postId/comments', async (req, res) => {
    const comment = new Comment({
        content: req.body.content,
        post: req.params.postId
    });

    try {
        const newComment = await comment.save();
        await Post.findByIdAndUpdate(req.params.postId, { $push: { comments: newComment._id } });
        res.status(201).json(newComment);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Upvote a comment
router.post('/posts/:postId/comments/:commentId/upvote', async (req, res) => {
    try {
        const comment = await Comment.findById(req.params.commentId);
        comment.upvotes += 1;
        await comment.save();
        res.json(comment);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Downvote a comment
router.post('/posts/:postId/comments/:commentId/downvote', async (req, res) => {
    try {
        const comment = await Comment.findById(req.params.commentId);
        comment.downvotes += 1;
        await comment.save();
        res.json(comment);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

module.exports = router;
