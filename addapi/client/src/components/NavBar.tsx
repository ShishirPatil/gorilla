import React from 'react';
import styled from 'styled-components';
import GitHubAuthButton from './GitHubAuthButton';
import { loginWithGithub } from '../api/apiService';

const NavbarContainer = styled.div`
  display: flex;
  justify-content: space-between; // Aligns children to both ends
  align-items: center;
  position: absolute;
  top: 0;
  right: 0; // Starts from the right end
  left: 0; // Spreads across the full width
  padding: 10px 20px;
  font-size: 18px;

  .nav-links {
    a:not(:last-child)::after {
        content: "|";
        margin: 0 10px;
        color: #000;
    }
  }
`;

interface NavBarProps {
    isLoggedIn: boolean;
    setIsLoggedIn: (isLoggedIn: boolean) => void;
}

const NavBar: React.FC<NavBarProps> = ({ isLoggedIn, setIsLoggedIn }) => {
    const handleLogin = () => {
        loginWithGithub();
    };

    const handleLogout = () => {
        localStorage.removeItem('accessToken');
        setIsLoggedIn(false);
    };

    return (
        <NavbarContainer>
            <GitHubAuthButton
                isLoggedIn={isLoggedIn}
                onLogin={handleLogin}
                onLogout={handleLogout}
            />
            <div className="nav-links">
                <a href="/index.html">Home</a>
                <a href="/blog.html">Blogs</a>
                <a href="/leaderboard.html">Leaderboard</a>
                <a href="/apizoo/">API Zoo Index</a>
            </div>
        </NavbarContainer>
    );
};

export default NavBar;
