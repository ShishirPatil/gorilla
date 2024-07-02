import React, { useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, useLocation } from 'react-router-dom';
import HomePage from './components/HomePage';
import AgentDetail from './components/AgentDetail';
import AddAgent from './components/AddAgent';
import FAQPage from './components/FAQPage';
import Login from './components/Login'; 
import Register from './components/Register'; 
import UserContext from './UserContext';
import PostDetail from './components/PostDetail';
import Forum from './components/Forum'
import ReactGA from 'react-ga4';

const App = () => {
  const [user, setUser] = React.useState(() => {
    // Retrieve user info from localStorage
    const savedUserInfo = localStorage.getItem('user-info');
    return savedUserInfo ? JSON.parse(savedUserInfo) : null;
  });

  const location = useLocation();

  useEffect(() => {
    ReactGA.send({ hitType: 'pageview', page: location.pathname + location.search });
  }, [location]);

  return (
    <UserContext.Provider value={{ user, setUser }}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/agents/:id" element={<AgentDetail />} />
        <Route path="/add-agent" element={<AddAgent />} />
        <Route path="/faqs" element={<FAQPage />} /> {/* FAQ Page Route */}
        <Route path="/login" element={<Login />} /> {/* Login Page Route */}
        <Route path="/register" element={<Register />} /> {/* Registration Page Route */}
        <Route path="/forum" element={<Forum />} />
        <Route path="/forum/posts/:postId" element={<PostDetail />} />
      </Routes>
    </UserContext.Provider>
  );
};

const AppWrapper = () => (
  <Router>
    <App />
  </Router>
);

export default AppWrapper;
