import React, { useState } from 'react';
import axios from 'axios';
import { Form, Button, Container } from 'react-bootstrap';
import {toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const RequestPasswordReset = () => {
  const [email, setEmail] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('https://agent-arena.vercel.app/api/auth/request-password-reset', { email });
      toast.success('Password reset link has been sent to your email');
    } catch (error) {
      console.error('Error requesting password reset', error);
      toast.error('An error occurred while requesting the password reset');
    }
  };

  return (
    <Container>
      <Form onSubmit={handleSubmit} className="mt-5">
        <Form.Group controlId="formEmail">
          <Form.Label>Email</Form.Label>
          <Form.Control type="email" placeholder="Enter your email" onChange={(e) => setEmail(e.target.value)} />
        </Form.Group>
        <Button variant="primary" type="submit" className="mt-4">
          Request Password Reset
        </Button>
      </Form>
    </Container>
  );
};

export default RequestPasswordReset;
