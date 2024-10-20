import React, { useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { Form, Button, Container } from 'react-bootstrap';
import {toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const ResetPassword = () => {
  const [password, setPassword] = useState('');
  const { token } = useParams();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`https://agent-arena.vercel.app/api/auth/reset-password/${token}`, { password });
      toast.success('Password has been reset successfully');
      navigate('/');  // Redirects to the base URL after successful reset
    } catch (error) {
      console.error('Error resetting password', error);
      toast.error('An error occurred while resetting your password');
    }
  };

  return (
    <Container>
      <Form onSubmit={handleSubmit} className="mt-5">
        <Form.Group controlId="formPassword">
          <Form.Label>New Password</Form.Label>
          <Form.Control type="password" placeholder="Enter new password" onChange={(e) => setPassword(e.target.value)} />
        </Form.Group>
        <Button variant="primary" type="submit" className="mt-4">
          Reset Password
        </Button>
      </Form>
    </Container>
  );
};

export default ResetPassword;
