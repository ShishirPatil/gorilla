import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Container, Row, Col, Card, Button, Form } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import Select from 'react-select';
import { toast} from 'react-toastify';
import { ThemeContext } from '../App';
import { Analytics } from "@vercel/analytics/react"


const UserList = () => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState('savedPrompts'); // Default sort by saved prompts
  const navigate = useNavigate();
  const { theme } = useContext(ThemeContext);

  
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('http://localhost:3001/api/users', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });

        console.log(response.data);

        // Sort users by saved prompts by default
        let sortedUsers = response.data.sort((a, b) => {
          const aLength = a.savedPrompts ? a.savedPrompts.length : 0;
          const bLength = b.savedPrompts ? b.savedPrompts.length : 0;
          return bLength - aLength;
        });
        

        // Ensure Nithik is placed in the third position only if the current third user has 0 saved prompts
        const nithikIndex = sortedUsers.findIndex(user => user.name === 'Nithik');
        const thirdUser = sortedUsers[2];

        if (nithikIndex !== -1 && thirdUser && thirdUser.savedPrompts.length === 0) {
          const [nithikUser] = sortedUsers.splice(nithikIndex, 1);
          sortedUsers.splice(2, 0, nithikUser); // Insert Nithik at the third position if third user has 0 saved prompts
        }

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
      users.filter(
        (user) =>
          user.name.toLowerCase().includes(query) ||
          user.bio.toLowerCase().includes(query) ||
          user.role.toLowerCase().includes(query)
      )
    );
  };

  const handleSortChange = (selectedOption) => {
    setSortOption(selectedOption.value);
    const sortedUsers = [...filteredUsers].sort((a, b) => {
      if (selectedOption.value === 'likes') return b.totalLikes - a.totalLikes;
      if (selectedOption.value === 'savedPrompts') return b.savedPrompts.length - a.savedPrompts.length;
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
            defaultValue={sortOptions[1]} // Default sort by saved prompts
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
                  {user.name}
                </Card.Title>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>
                  {user.bio}
                </Card.Text>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>
                  Role: {user.role}
                </Card.Text>
                <Card.Text className={theme === 'dark' ? 'text-white' : 'text-dark'}>
                  Saved Prompts: {user.savedPrompts.length}
                </Card.Text>
                <div className="mt-auto">
                  <div className="d-flex justify-content-center mb-3">
                    <Button variant="outline-success" onClick={notifyLikesDislikes}>
                      Total Likes: ({user.totalLikes})
                    </Button>
                    <Button variant="outline-danger" onClick={notifyLikesDislikes}>
                      Total Dislikes: ({user.totalDislikes})
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
