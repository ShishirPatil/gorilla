import React, { useState, useContext } from 'react';
import '../App.css';
import { useNavigate } from 'react-router-dom';
import UserContext from '../UserContext';


const Register = () => {
    const navigate = useNavigate();
    const { setUser } = useContext(UserContext); // Use this if you're managing user state globally
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();
        const userData = { name, email, password };
    
        try {
            const response = await fetch('https://agent-marketplace-2jmb.vercel.app/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
            const data = await response.json();
            console.log(data);
            if (data.status === 'ok') {
                // Assume response includes the token and email if registration is successful
                localStorage.setItem('user-info', JSON.stringify({ email, token: data.token, name:data.name }));
                
                // Set user in UserContext
                setUser({ email, token: data.token, name:data.name});

                console.log('Registration successful', data);
                navigate('/'); // This will navigate to the homepage
            } else {
                console.error('Registration failed', data.message);
                // Optionally handle registration errors (e.g., display an error message)
            }
        } catch (error) {
            console.error('There was a problem with the registration:', error);
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
            <button onClick={() => navigate(-1)} style={backButtonStyle}>← Go Back</button>

            <h2>Register</h2>
            <form onSubmit={handleSubmit} className="auth-form">
                <div className="input-group">
                    <label htmlFor="name">Name</label>
                    <input
                        type="text"
                        id="name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>
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
                <button type="submit" className="auth-button">Register</button>
            </form>
        </div>
        </div>
        </>
    );
};

export default Register;
