import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import UserContext from '../UserContext';
import '../App.css';
import { FaThumbsUp, FaThumbsDown, FaCommentAlt } from 'react-icons/fa'; // Importing icons

const PostDetail = () => {
    const { postId } = useParams();
    const [post, setPost] = useState(null);
    const [newComment, setNewComment] = useState('');
    const { user } = useContext(UserContext);
    const navigate = useNavigate();

    useEffect(() => {
        fetchPost();
    }, []);
    axios.defaults.baseURL = 'https://agent-marketplace-2jmb.vercel.app/api';

    const fetchPost = async () => {
        try {
            const response = await axios.get(`/forum/posts/${postId}`);
            setPost(response.data);
        } catch (error) {
            console.error('Error fetching post:', error);
        }
    };

    const handleNewComment = async () => {
        try {
            await axios.post(`/forum/posts/${postId}/comments`, { content: newComment });
            fetchPost();
            setNewComment('');
        } catch (error) {
            console.error('Error adding a new comment:', error);
        }
    };

    const handleUpvotePost = async () => {
        try {
            await axios.post(`/forum/posts/${postId}/upvote`);
            fetchPost();
        } catch (error) {
            console.error('Error upvoting post:', error);
        }
    };

    const handleDownvotePost = async () => {
        try {
            await axios.post(`/forum/posts/${postId}/downvote`);
            fetchPost();
        } catch (error) {
            console.error('Error downvoting post:', error);
        }
    };

    const handleUpvoteComment = async (commentId) => {
        try {
            await axios.post(`/forum/posts/${postId}/comments/${commentId}/upvote`);
            fetchPost();
        } catch (error) {
            console.error('Error upvoting comment:', error);
        }
    };

    const handleDownvoteComment = async (commentId) => {
        try {
            await axios.post(`/forum/posts/${postId}/comments/${commentId}/downvote`);
            fetchPost();
        } catch (error) {
            console.error('Error downvoting comment:', error);
        }
    };

    return (
        <div style={{ maxWidth: '800px', margin: '60px auto', padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '10px', boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)' }}>
            <button onClick={() => navigate(-1)} style={{ padding: '10px 20px', margin: '20px 0', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem', minWidth: '100px', minHeight: '40px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px' }}>← Go Back</button>

            {post ? (
                <>
                    <h3>{post.title}</h3>
                    <p>{post.content}</p>
                    <div className="voteButtonsContainer">
                        <button className="voteButton" onClick={(e) => { e.stopPropagation(); handleUpvotePost(post._id); }}>
                                            <FaThumbsUp style={{ color: '#007bff' }} /> <span style={{ color: '#007bff' }}>Upvote ({post.upvotes})</span>
                        </button>
                        <button className="voteButton" onClick={(e) => { e.stopPropagation(); handleDownvotePost(post._id); }}>
                                            <FaThumbsDown style={{ color: 'red' }} /> <span style={{ color: 'red' }}>Downvote ({post.downvotes})</span>
                        </button>
                        <button className="voteButton" style={{color: 'black'}}>
                                        <FaCommentAlt /> <span style={{ color: 'black' }}>Comments ({post.comments.length})</span> 
                        </button>
                    </div>
                    <div className="commentsSection" style={{ maxHeight: '300px', overflowY: 'auto', flex: 'wrap'}}>
                        {post.comments.map(comment => (
                            <div key={comment._id} className="comment" style={{ maxHeight: '300px', overflowY: 'auto', flex: 'wrap'}}>
                                <p>{comment.content}</p>
                                <div className="voteButtonsContainer">
                                <button className="voteButton" onClick={() => handleUpvoteComment(comment._id)} style={{color: '#007bff'}}><FaThumbsUp style={{ color: '#007bff' }} /> <span style={{ color: '#007bff' }}>Upvote ({comment.upvotes})</span></button>
                                <button className="voteButton" onClick={() => handleDownvoteComment(comment._id)} style={{color: 'red'}}><FaThumbsDown style={{ color: 'red' }} /> <span style={{ color: 'red' }}>Downvote ({comment.downvotes})</span></button>
                                </div>

                            </div>
                        ))}
                    </div>
                    <input
                        type="text"
                        className="inputField"
                        value={newComment}
                        style={{ marginTop: '20px'}} // Adjusted margin
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="New Comment"
                    />
                    <button className="button" onClick={handleNewComment}>Add Comment</button>
                </>
            ) : (
                <p>Loading post...</p>
            )}
        </div>
    );
};

export default PostDetail;
