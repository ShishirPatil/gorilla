import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Container, Row, Col, Card, Button, Form } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import Select from 'react-select';
import { toast } from 'react-toastify';
import { ThemeContext } from '../App';
import { Analytics } from "@vercel/analytics/react"

const UserList = () => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState('likes'); // Default sort by likes
  const navigate = useNavigate();
  const { theme } = useContext(ThemeContext);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('https://agent-arena.vercel.app/api/users', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });

        console.log(response.data);

        // Sort users by likes by default, with saved prompts as secondary criterion
        let sortedUsers = response.data.sort((a, b) => {
          const likeDiff = (b.totalLikes || 0) - (a.totalLikes || 0);
          if (likeDiff !== 0) return likeDiff;
          return (b.savedPrompts?.length || 0) - (a.savedPrompts?.length || 0);
        });

        setUsers(sortedUsers);
        setFilteredUsers(sortedUsers);
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
    const query = e.target.value.toLowerCase();
    setSearchQuery(query);
    setFilteredUsers(
      users.filter((user) => {
        const nameMatch = user.name?.toLowerCase().includes(query) || false;
        const bioMatch = user.bio?.toLowerCase().includes(query) || false;
        const roleMatch = user.role?.toLowerCase().includes(query) || false;
        return nameMatch || bioMatch || roleMatch;
      })
    );
  };

  const handleSortChange = (selectedOption) => {
    setSortOption(selectedOption.value);
    const sortedUsers = [...filteredUsers].sort((a, b) => {
      if (selectedOption.value === 'likes') {
        const likeDiff = (b.totalLikes || 0) - (a.totalLikes || 0);
        if (likeDiff !== 0) return likeDiff;
        return (b.savedPrompts?.length || 0) - (a.savedPrompts?.length || 0);
      }
      if (selectedOption.value === 'savedPrompts') {
        const promptDiff = (b.savedPrompts?.length || 0) - (a.savedPrompts?.length || 0);
        if (promptDiff !== 0) return promptDiff;
        return (b.totalLikes || 0) - (a.totalLikes || 0);
      }
      return 0;
    });
    setFilteredUsers(sortedUsers);
  };

  const notifyLikesDislikes = () => {
    toast.info('You must like a specific prompt by the user. Click "View Prompts" to do so.');
  };

  const sortOptions = [
    { value: 'likes', label: 'Total Likes' },
    { value: 'savedPrompts', label: 'Saved Prompts' },
  ];

  return (
    <Container className="mt-4">
      <Analytics />
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
          />
        </Col>
        <Col md={6}>
          <Select
            options={sortOptions}
            onChange={handleSortChange}
            placeholder="Sort by..."
            defaultValue={sortOptions[0]} // Default sort by likes
          />
        </Col>
      </Row>
      <Row>
        {filteredUsers.map((user) => (
          <Col key={user._id} md={4} className="mb-4">
            <Card
              className="h-100"
              style={{
                backgroundColor: theme === 'dark' ? '#1c1c1e' : '#ffffff',
                borderColor: theme === 'dark' ? '#4a4a4c' : '#e0e0e0',
              }}
            >
              <Card.Body className="d-flex flex-column">
                <Card.Title className={theme === 'dark' ? 'text-white' : 'text-dark'}>
                  {user.name || ''}
                </Card.Title>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>
                  {user.bio || ''}
                </Card.Text>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>
                  Role: {user.role || ''}
                </Card.Text>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>
                  Saved Prompts: {user.savedPrompts?.length || 0}
                </Card.Text>
                <div className="mt-auto">
                  <div className="d-flex justify-content-center mb-3">
                    <Button variant="outline-success" onClick={notifyLikesDislikes}>
                      Total Likes: ({user.totalLikes || 0})
                    </Button>
                    <Button variant="outline-danger" onClick={notifyLikesDislikes}>
                      Total Dislikes: ({user.totalDislikes || 0})
                    </Button>
                  </div>
                  <Button variant="primary" onClick={() => viewUserPrompts(user._id)} className="w-100">
                    View Prompts
                  </Button>
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