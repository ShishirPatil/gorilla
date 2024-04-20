// GitHubAuthButton.tsx
import React from 'react';

interface GitHubAuthButtonProps {
  isLoggedIn: boolean;
  onLogin: () => void;
  onLogout: () => void;
}

const GitHubAuthButton: React.FC<GitHubAuthButtonProps> = ({ isLoggedIn, onLogin, onLogout }) => {
  return (
    <button
      className="btn btn-db btn-ex"
      onClick={isLoggedIn ? onLogout : onLogin}
      aria-live="polite"
    >
      {isLoggedIn ? 'Logout' : 'Login with GitHub'}
    </button>
  );
};

export default GitHubAuthButton;
