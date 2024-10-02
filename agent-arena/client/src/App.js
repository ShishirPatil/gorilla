import React, { useState, useEffect, createContext, useCallback, useContext } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
import AgentArena from './components/AgentArena';
import UserProfile from './components/UserProfile';
import SignUp from './components/SignUp';
import Login from './components/Login';
import UserList from './components/UserList';
import UserPrompts from './components/UserPrompts';
import PromptDetail from './components/PromptDetail';
import ContactUs from './components/ContactUs';
import Leaderboard from './components/Leaderboard';
import FAQ from './components/FAQ';  
import { Container, Navbar, Nav, Button } from 'react-bootstrap';
import RequestPasswordReset from './components/RequestPasswordReset';
import ResetPassword from './components/ResetPassword';
import 'bootstrap/dist/css/bootstrap.min.css';
import { ToastContainer } from 'react-toastify';
import { FiSun, FiMoon } from 'react-icons/fi';
import MonitoringDashboard from './components/MonitoringDashboard';

import 'react-toastify/dist/ReactToastify.css';
import './App.css';

export const ThemeContext = createContext();

const App = () => {

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [theme, setTheme] = useState('light');

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

    const savedTheme = localStorage.getItem('theme') || 'light';
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
          <NavbarComponent 
            theme={theme} 
            isAuthenticated={isAuthenticated} 
            handleLogout={handleLogout} 
          />
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
              <Route path="/request-password-reset" element={<RequestPasswordReset />} />
              <Route path="/reset-password/:token" element={<ResetPassword />} />
              <Route path="/faq" element={<FAQ />} /> {/* Add the FAQ route */}
              <Route path="/contact-us" element={<ContactUs />} /> {/* Add the Contact Us route */}
              <Route path="/dashboard" element={<MonitoringDashboard />} /> 
            </Routes>
            <ToastContainer />
          </Container>
        </Router>
      </div>
    </ThemeContext.Provider>
  );
};

// NavbarComponent is placed inside Router so useLocation works here
const NavbarComponent = ({ theme, isAuthenticated, handleLogout }) => {
  const location = useLocation(); // Now it is inside Router, so useLocation will work

  const handleAgentArenaClick = (e) => {
    if (location.pathname === '/') {
      e.preventDefault();
      window.location.reload();
    }
  };

  const ThemeToggle = () => {
    const { toggleTheme } = useContext(ThemeContext);
  
    return (
      <Nav.Link 
        onClick={toggleTheme}
        className="d-flex align-items-center"
        style={{ padding: '0.5rem 0.5rem', marginLeft: '0.5rem' }}
      >
        <div 
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            backgroundColor: theme === 'dark' ? '#4a4a4a' : '#e0e0e0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background-color 0.3s ease'
          }}
        >
          {theme === 'dark' ? 
            <FiSun color="#f1c40f" size={18} /> : 
            <FiMoon color="#34495e" size={18} />
          }
        </div>
      </Nav.Link>
    );
  };

  return (
    <Navbar bg={theme === 'dark' ? 'dark' : 'light'} variant={theme === 'dark' ? 'dark' : 'light'} expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand 
          as={Link} 
          to="/" 
          onClick={handleAgentArenaClick} // Handle reload logic on brand click
          style={{ display: 'flex', flexDirection: 'column', color: theme === 'dark' ? '#ffffff' : '#007bff', textAlign: 'center' }}
        >
          <span>Agent Arena</span>
          <span style={{ fontSize: '12px', color: theme === 'dark' ? '#b3b3b3' : '#6c757d' , textAlign:'center'}}>🦍 Gorilla&nbsp;X&nbsp;LMSYS Chatbot Arena</span>
        </Navbar.Brand>

        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link 
              as={Link} 
              to="/" 
              onClick={handleAgentArenaClick} // Handle reload logic on nav link click
            >
              Arena
            </Nav.Link>
            <Nav.Link as={Link} to="/leaderboard">Leaderboard</Nav.Link>
            <Nav.Link as={Link} to="/users">Prompt Hub</Nav.Link>
            <Nav.Link as={Link} to="https://www.llm-agents.info/">Agent Marketplace</Nav.Link>
            <Nav.Link as={Link} to="/faq">FAQ</Nav.Link>
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

            <ThemeToggle />


          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default App;
