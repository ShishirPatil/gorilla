import React, { useState, useContext } from 'react';
import { Container, Row, Col, Form, Button } from 'react-bootstrap';
import { ThemeContext } from '../App';
import { toast } from 'react-toastify';
import axios from 'axios';

const ContactUs = () => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const { theme } = useContext(ThemeContext);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await axios.post('https://agent-arena.vercel.app/api/contact/submit', formData);
      
      if (response.status === 200) {
        toast.success('Your inquiry has been sent. We will get back to you soon!');
        setFormData({ name: '', email: '', message: '' });
      }
    } catch (error) {
      console.error('Error submitting inquiry:', error);
      toast.error('There was an error sending your inquiry. Please try again later.');
    }
  };

  const styles = {
    container: {
      paddingTop: '3rem',
      paddingBottom: '3rem',
      backgroundColor: theme === 'dark' ? '#1a1a2e' : '#f8f9fa',
      color: theme === 'dark' ? '#e0e0e0' : '#333',
      minHeight: 'calc(100vh - 60px)',
    },
    formContainer: {
      backgroundColor: theme === 'dark' ? '#242e42' : '#ffffff',
      padding: '2rem',
      borderRadius: '10px',
      boxShadow: theme === 'dark' ? '0 4px 6px rgba(0, 0, 0, 0.2)' : '0 4px 6px rgba(0, 0, 0, 0.1)',
    },
    title: {
      color: theme === 'dark' ? '#81a1c1' : '#2c3e50',
      marginBottom: '1.5rem',
    },
    description: {
      color: theme === 'dark' ? '#d8dee9' : '#555',
      marginBottom: '2rem',
    },
    label: {
      color: theme === 'dark' ? '#81a1c1' : '#2c3e50',
      fontWeight: 'bold',
    },
    input: {
        backgroundColor: theme === 'dark' ? '#ccdaf0' : '#f8f9fa',
        color: theme === 'dark' ? '#333' : '#333', 
        border: theme === 'dark' ? '1px solid #3b4252' : '1px solid #ced4da',
      },
    button: {
      backgroundColor: theme === 'dark' ? '#5e81ac' : '#2c3e50',
      borderColor: theme === 'dark' ? '#5e81ac' : '#2c3e50',
      color: '#ffffff',
      padding: '0.5rem 2rem',
      fontSize: '1.1rem',
      marginTop: '1rem',
      transition: 'all 0.3s ease',
    },
  };

  return (
    <div style={styles.container}>
      <Container>
        <Row className="justify-content-center">
          <Col md={8} lg={6}>
            <div style={styles.formContainer}>
              <h1 className="text-center" style={styles.title}>Contact Us</h1>
              <p className="text-center" style={styles.description}>
                If you have any questions, suggestions, or would like to contribute agents or models, please fill out the form below, and we'll get back to you shortly.
              </p>

              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3" controlId="formName">
                  <Form.Label style={styles.label}>Your Name</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter your name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                    style={styles.input}
                  />
                </Form.Group>

                <Form.Group className="mb-3" controlId="formEmail">
                  <Form.Label style={styles.label}>Your Email</Form.Label>
                  <Form.Control
                    type="email"
                    placeholder="Enter your email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                    style={styles.input}
                  />
                </Form.Group>

                <Form.Group className="mb-4" controlId="formMessage">
                  <Form.Label style={styles.label}>Your Message</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={4}
                    placeholder="Enter your message"
                    name="message"
                    value={formData.message}
                    onChange={handleInputChange}
                    required
                    style={styles.input}
                  />
                </Form.Group>

                <div className="d-flex justify-content-center">
                  <Button type="submit" style={styles.button}>
                    Submit
                  </Button>
                </div>
              </Form>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default ContactUs;