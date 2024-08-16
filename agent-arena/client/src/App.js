import React, { useState, useEffect, createContext, useCallback } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import AgentArena from './components/AgentArena';
import UserProfile from './components/UserProfile';
import SignUp from './components/SignUp';
import Login from './components/Login';
import UserList from './components/UserList';
import UserPrompts from './components/UserPrompts';
import PromptDetail from './components/PromptDetail';
import Leaderboard from './components/Leaderboard';
import { Container, Navbar, Nav, Button } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

export const ThemeContext = createContext();

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [theme, setTheme] = useState('dark');

  const applyTheme = useCallback((newTheme) => {
    const linkId = 'dynamic-theme';
    const existingLink = document.getElementById(linkId);

    if (existingLink) {
      document.head.removeChild(existingLink);
    }

    const link = document.createElement('link');
    link.id = linkId;
    link.rel = 'stylesheet';
    link.href = `/${newTheme}-theme.css`;
    document.head.appendChild(link);

    document.body.className = newTheme + '-theme';
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }

    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    applyTheme(savedTheme);
  }, [applyTheme]);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <div className={theme + '-theme'}>
        <Router>
          <Navbar bg={theme === 'dark' ? 'dark' : 'light'} variant={theme === 'dark' ? 'dark' : 'light'} expand="lg" className="mb-4">
            <Container>
              <Navbar.Brand as={Link} to="/">LLM Agent Arena</Navbar.Brand>
              <Navbar.Toggle aria-controls="basic-navbar-nav" />
              <Navbar.Collapse id="basic-navbar-nav">
                <Nav className="ms-auto">
                  <Nav.Link as={Link} to="/">Arena</Nav.Link>
                  <Nav.Link as={Link} to="/leaderboard">Leaderboard</Nav.Link>
                  <Nav.Link as={Link} to="/users">Prompt Hub</Nav.Link>
                  <Nav.Link as={Link} to="https://www.llm-agents.info/" target="_blank">Agent Marketplace</Nav.Link>
                  {isAuthenticated ? (
                    <>
                      <Nav.Link as={Link} to="/profile">Profile/Prompts</Nav.Link>
                      <Button variant={theme === 'dark' ? 'outline-light' : 'outline-dark'} onClick={handleLogout}>Logout</Button>
                    </>
                  ) : (
                    <>
                      <Nav.Link as={Link} to="/login">Login</Nav.Link>
                    </>
                  )}
                  <Button variant={theme === 'dark' ? 'outline-light' : 'outline-dark'} onClick={toggleTheme}>
                    {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                  </Button>
                </Nav>
              </Navbar.Collapse>
            </Container>
          </Navbar>
          <Container>
            <Routes>
              <Route path="/" element={<AgentArena />} />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/users" element={<UserList />} />
              <Route path="/user/:userId" element={<UserPrompts />} />
              <Route path="/login" element={<Login onLogin={() => setIsAuthenticated(true)} />} />
              <Route path="/signup" element={<SignUp onSignUp={() => setIsAuthenticated(true)} />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/prompts/:promptId" element={<PromptDetail />} />
            </Routes>
            <ToastContainer />
          </Container>
        </Router>
      </div>
    </ThemeContext.Provider>
  );
};

export default App;