import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom'; 
import UserContext from '../UserContext'; 

import '../App.css';

const Login = () => {
    const navigate = useNavigate();
    const { user, setUser } = useContext(UserContext);
    const [email, setEmail] = useState('');
    const [name, setName] = useState('');

    const [password, setPassword] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();

        try {
            const response = await fetch('https://agent-marketplace-2jmb.vercel.app/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();
            console.log(data);
            if (response.ok) {
                // Save user information and token to localStorage
                localStorage.setItem('user-info', JSON.stringify({ email, token: data.token, name: data.name }));
                
                // Set user in UserContext
                setUser({ email, token: data.token, name:data.name});
                
                // Navigate to the home page or dashboard
                navigate('/');
                
            } else {
                console.error('Login failed:', data.message);
            }
        } catch (error) {
            console.error('There was a problem with the login:', error);
        }
    };
    const containerStyle = {
        marginTop: '60px', // Add margin-top to push down the content below the navbar
    };
    const backButtonStyle = {
        padding: '10px 20px', 
        margin: '0 0 20px', 
        cursor: 'pointer',
        fontWeight: 'bold',
        fontSize: '1rem', // Use 'rem' units for scalable font size
        minWidth: '100px', // Minimum width so the button doesn't become too small
        minHeight: '40px', // Minimum height for the same reason
      };

    return (
        <>
        <div style={containerStyle}>

        <h1 style={{ textAlign: 'center', fontSize: '2.5rem', margin: '0 0 10px 0', color: '#007bff' }}>Agents Marketplace</h1>
        <div className="auth-container">
            <button onClick={() => navigate('/')} style={backButtonStyle}>← Go Back</button>

            <h2>Login</h2>
            <form onSubmit={handleSubmit} className="auth-form">
                <div className="input-group">
                    <label htmlFor="email">Email</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div className="input-group">
                    <label htmlFor="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit" className="auth-button">Login</button>
            </form>
            <p className="auth-switch">
                New to this page? <Link to="/register">Sign up</Link> to get started.
            </p>
        </div>
        </div>
        </>
    );
};

export default Login;
