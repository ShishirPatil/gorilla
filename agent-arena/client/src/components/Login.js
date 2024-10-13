import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Button, Container } from 'react-bootstrap';
import {toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('https://agent-arena.vercel.app/api/auth/login', formData);
      localStorage.setItem('token', response.data.token);
      onLogin();
      navigate('/');
    } catch (error) {
      console.error('Error logging in', error);
      if (error.response && error.response.status === 400) {
        toast.error('Invalid email or password');
      } else {
        toast.error('An error occurred during login');
      }
    }
  };

  return (
    <Container>
      <Form onSubmit={handleSubmit} className="mt-5">
        <Form.Group controlId="formEmail">
          <Form.Label>Email</Form.Label>
          <Form.Control type="email" name="email" placeholder="Enter email" onChange={handleChange} />
        </Form.Group>
        <Form.Group controlId="formPassword" className="mt-3">
          <Form.Label>Password</Form.Label>
          <Form.Control type="password" name="password" placeholder="Password" onChange={handleChange} />
        </Form.Group>
        <Button variant="primary" type="submit" className="mt-4">
          Login
        </Button>
      </Form>
      <p className="mt-3 text-center">
        Don't have an account? <Link to="/signup" className="btn btn-link p-0 m-0 align-baseline">Sign up here</Link>
      </p>
      <p className="text-center">
        <Link to="/request-password-reset" className="btn btn-link p-0 m-0 align-baseline">Forgot Password?</Link>
      </p>
    </Container>
  );
};

export default Login;
