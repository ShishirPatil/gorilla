import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import UserContext from '../UserContext';
import { FaThumbsUp, FaThumbsDown, FaCommentAlt } from 'react-icons/fa';
import '../App.css';
import './Nav.css'; // Import the CSS file

// Set the base URL for Axios
axios.defaults.baseURL = 'https://agent-marketplace-2jmb.vercel.app/api';

const Forum = () => {
    const [posts, setPosts] = useState([]);
    const [newPostTitle, setNewPostTitle] = useState('');
    const [newPostContent, setNewPostContent] = useState('');
    const { user, setUser } = useContext(UserContext);
    const navigate = useNavigate();
    const [sortOption, setSortOption] = useState('newest');

    useEffect(() => {
        fetchPosts();
    }, [sortOption]);

    const fetchPosts = async () => {
        try {
            const response = await axios.get('/forum/posts');
            let fetchedPosts = Array.isArray(response.data) ? response.data : [];
            
            // Sort posts based on the selected option
            if (sortOption === 'mostUpvotes') {
                fetchedPosts.sort((a, b) => b.upvotes - a.upvotes);
            } else if (sortOption === 'mostComments') {
                fetchedPosts.sort((a, b) => b.comments.length - a.comments.length);
            } else {
                fetchedPosts.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
            }

            setPosts(fetchedPosts);
        } catch (error) {
            console.error('Error fetching posts:', error);
            setPosts([]);
        }
    };

    const handleNewPost = async () => {
        try {
            const response = await axios.post('/forum/posts', { title: newPostTitle, content: newPostContent });
            setPosts([...posts, response.data]);
            setNewPostTitle('');
            setNewPostContent('');
        } catch (error) {
            console.error('Error creating a new post:', error);
        }
    };

    const handleUpvotePost = async (postId) => {
        try {
            await axios.post(`/forum/posts/${postId}/upvote`);
            fetchPosts();
        } catch (error) {
            console.error('Error upvoting post:', error);
        }
    };

    const handleDownvotePost = async (postId) => {
        try {
            await axios.post(`/forum/posts/${postId}/downvote`);
            fetchPosts();
        } catch (error) {
            console.error('Error downvoting post:', error);
        }
    };

    const handleLogout = () => {
        setUser(null);
        localStorage.removeItem('user-info');
        navigate('/login');
    };

    const navigateToAddAgent = () => {
        navigate('/add-agent');
    };

    const navigateToPost = (postId) => {
        navigate(`/forum/posts/${postId}`);
    };

    const handleSortChange = (e) => {
        setSortOption(e.target.value);
    };

    return (
        <>
            <div style={{ maxWidth: '1200px', margin: '60px auto' }}>
                <div className={`navButtonsContainer ${window.innerWidth <= 768 ? 'mobile' : ''}`} style={{ justifyContent: 'flex-end', marginBottom: '20px' }}>
                    <button onClick={() => navigate('/')} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Home</button>
                    {user ? (
                        <>
                            <button onClick={handleLogout} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Logout</button>
                            <button onClick={() => navigate('/my-agents')} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Show My Agents</button>
                        </>
                    ) : (
                        <button onClick={() => navigate('/login')} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Login</button>
                    )}
                    <button onClick={navigateToAddAgent} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Add New Agent</button>
                    <button onClick={() => navigate('/faqs')} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>FAQs</button>
                    <button onClick={() => window.location.href = 'https://gorilla.cs.berkeley.edu/blogs/11_agent_marketplace.html'} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Blog</button>
                    <button onClick={() => navigate('/forum')} className={`navButton ${window.innerWidth <= 768 ? 'mobile' : ''}`}>Forum</button>
                </div>
            </div>

            <div style={{ maxWidth: '800px', margin: '20px auto', padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '10px', boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)' }}>
                <h1 className="title">Forum</h1>
                <p className="subtitle">Share your ideas and feedback, and engage with the community.</p>

                <div>
                    <h2>New Post</h2>
                    <input
                        type="text"
                        className="inputField"
                        value={newPostTitle}
                        onChange={(e) => setNewPostTitle(e.target.value)}
                        placeholder="Title"
                    />
                    <textarea
                        className="inputField"
                        value={newPostContent}
                        onChange={(e) => setNewPostContent(e.target.value)}
                        placeholder="Content"
                    />
                    <button className="button" style={{ marginBottom: '20px' }} onClick={handleNewPost}>Submit</button>
                </div>

                <div>
                    <select value={sortOption} onChange={handleSortChange} style={{ marginBottom: '20px', padding: '10px', border: '1px solid #007bff', borderRadius: '5px', backgroundColor: 'white', color: '#007bff' }}>
                        <option value="newest">Newest</option>
                        <option value="mostUpvotes">Most Upvotes</option>
                        <option value="mostComments">Most Comments</option>
                    </select>
                </div>

                <div>
                    {posts.length > 0 ? (
                        posts.map(post => (
                            <div key={post._id} className="post hoverable" onClick={() => navigateToPost(post._id)} style={{ cursor: 'pointer', marginBottom: '20px' }}>
                                <h3>{post.title}</h3>
                                <p>{post.content}</p>
                                <div className="voteButtonsContainer">
                                    <button className="voteButton" onClick={(e) => { e.stopPropagation(); handleUpvotePost(post._id); }}>
                                        <FaThumbsUp style={{ color: '#007bff' }} /> <span style={{ color: '#007bff' }}>Upvote ({post.upvotes})</span>
                                    </button>
                                    <button className="voteButton" onClick={(e) => { e.stopPropagation(); handleDownvotePost(post._id); }}>
                                        <FaThumbsDown style={{ color: 'red' }} /> <span style={{ color: 'red' }}>Downvote ({post.downvotes})</span>
                                    </button>
                                    <button className="voteButton" onClick={(e) => { e.stopPropagation(); navigateToPost(post._id); }}>
                                        <FaCommentAlt /> <span style={{ color: 'black' }}>Comments ({post.comments.length})</span> 
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p>No posts available</p>
                    )}
                </div>
            </div>
        </>
    );
};

export default Forum;
