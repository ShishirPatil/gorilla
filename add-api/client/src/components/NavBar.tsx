import React from 'react';
import styled from 'styled-components';

const NavbarContainer = styled.div`
    position: absolute;
    top: 0;
    right: 20px;
    padding: 10px;
    z-index: 100;
    font-size: 18px;

    a:not(:last-child)::after {
        content: "|";
        margin: 0 10px;
        color: #000;
    }
`;

// Define the component
const NavBar: React.FC = () => {
    return (
        <NavbarContainer>
            <a href="/index.html">Home</a>
            <a href="/blog.html">Blogs</a>
            <a href="/leaderboard.html">Leaderboard</a>
            <a href="/apizoo/">API Zoo Index</a>
        </NavbarContainer>
    );
};

export default NavBar;
