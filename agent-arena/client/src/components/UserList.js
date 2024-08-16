import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Card, Button, Container, Row, Col, Form } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import Select from 'react-select';
import { ThemeContext } from '../App'; // Import ThemeContext from App

const UserList = () => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState('');
  const navigate = useNavigate();
  const { theme } = useContext(ThemeContext); // Get the current theme

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('https://agent-arena.vercel.app/api/users', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setUsers(response.data);
        setFilteredUsers(response.data);
      } catch (error) {
        console.error('Error fetching users:', error);
      }
    };

    fetchUsers();
  }, []);

  const viewUserPrompts = (userId) => {
    navigate(`/user/${userId}`);
  };

  const handleSearch = (e) => {
    setSearchQuery(e.target.value);
    const query = e.target.value.toLowerCase();
    setFilteredUsers(users.filter(user => 
      user.name.toLowerCase().includes(query) || 
      user.bio.toLowerCase().includes(query) || 
      user.role.toLowerCase().includes(query)
    ));
  };

  const handleSortChange = (selectedOption) => {
    setSortOption(selectedOption.value);
    let sortedUsers;
    if (selectedOption.value === 'likes') {
      sortedUsers = [...filteredUsers].sort((a, b) => b.totalLikes - a.totalLikes);
    } else if (selectedOption.value === 'savedPrompts') {
      sortedUsers = [...filteredUsers].sort((a, b) => b.savedPrompts.length - a.savedPrompts.length);
    }
    setFilteredUsers(sortedUsers);
  };

  const sortOptions = [
    { value: 'likes', label: 'Total Likes' },
    { value: 'savedPrompts', label: 'Saved Prompts' },
  ];

  const customStyles = {
    control: (base) => ({
      ...base,
      minHeight: 40,
      fontSize: 14,
      width: '100%',
    }),
    menu: (base) => ({
      ...base,
      fontSize: 14,
    }),
    singleValue: (base) => ({
      ...base,
      color: '#4b0082',
    }),
    option: (base, { isFocused }) => ({
      ...base,
      color: '#4b0082',
      backgroundColor: isFocused ? '#d3d3d3' : 'white',
    }),
  };

  return (
    <Container className="mt-4">
      <h1 className="text-center mb-4">Users</h1>
      <p className="text-center mb-4">
        Explore the users of the LLM Agent Arena platform. Click on "View Prompts" to see the prompts they've saved, 
        along with likes and dislikes. This can help you find interesting prompts and understand which agents work best for certain tasks.
      </p>
      <Row className="mb-4">
        <Col md={6}>
          <Form.Control
            type="text"
            placeholder="Search users..."
            value={searchQuery}
            onChange={handleSearch}
            className="mb-4"
          />
        </Col>
        <Col md={6}>
          <Select
            options={sortOptions}
            onChange={handleSortChange}
            placeholder="Sort by..."
            styles={customStyles}
          />
        </Col>
      </Row>
      <Row>
        {filteredUsers.map(user => (
          <Col key={user._id} md={4} className="mb-4">
            <Card className="h-100" style={{
              backgroundColor: theme === 'dark' ? '#1c1c1e' : '#ffffff',
              borderColor: theme === 'dark' ? '#4a4a4c' : '#e0e0e0'
            }}>
              <Card.Body className="d-flex flex-column">
                <Card.Title className={theme === 'dark' ? 'text-white' : 'text-dark'}>{user.name}</Card.Title>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>{user.bio}</Card.Text>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>Role: {user.role}</Card.Text>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>Saved Prompts: {user.savedPrompts.length}</Card.Text>
                <div className="mt-auto">
                  <div className="d-flex justify-content-center mb-3">
                    <Button variant="outline-success" className="mr-2">Total Likes: ({user.totalLikes})</Button>
                    <Button variant="outline-danger">Total Dislikes: ({user.totalDislikes})</Button>
                  </div>
                  <Button variant="primary" onClick={() => viewUserPrompts(user._id)} className="w-100">View Prompts</Button>
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </Container>
  );
};

export default UserList;
