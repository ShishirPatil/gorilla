import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Form, Button, Container, Alert } from 'react-bootstrap';

const SignUp = ({ onSignUp }) => {
  const [formData, setFormData] = useState({ name: '', email: '', password: '', bio: '', role: '' });
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('https://agent-arena.vercel.app/api/auth/signup', formData);
      localStorage.setItem('token', response.data.token);
      onSignUp();
      navigate('/');
    } catch (error) {
      setErrorMessage(error.response.data.message || 'Error signing up');
    }
  };

  return (
    <Container>
      <Form onSubmit={handleSubmit} className="mt-5">
        {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
        <Form.Group controlId="formName">
          <Form.Label>Name</Form.Label>
          <Form.Control type="text" name="name" placeholder="Name" onChange={handleChange} />
        </Form.Group>
        <Form.Group controlId="formEmail" className="mt-3">
          <Form.Label>Email</Form.Label>
          <Form.Control type="email" name="email" placeholder="Email" onChange={handleChange} />
        </Form.Group>
        <Form.Group controlId="formPassword" className="mt-3">
          <Form.Label>Password</Form.Label>
          <Form.Control type="password" name="password" placeholder="Password" onChange={handleChange} />
        </Form.Group>
        <Form.Group controlId="formBio" className="mt-3">
          <Form.Label>Bio</Form.Label>
          <Form.Control type="text" name="bio" placeholder="Bio" onChange={handleChange} />
        </Form.Group>
        <Form.Group controlId="formRole" className="mt-3">
          <Form.Label>Role</Form.Label>
          <Form.Control type="text" name="role" placeholder="Role (e.g., PhD student)" onChange={handleChange} />
        </Form.Group>
        <Button variant="primary" type="submit" className="mt-4">
          Sign Up
        </Button>
      </Form>
    </Container>
  );
};

export default SignUp;
