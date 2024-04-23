import { useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

import Header from './components/Header';
import Dashboard from './components/Dashboard';
import NavBar from './components/NavBar';
import { ToastContainer } from 'react-toastify';
import { checkAccessToken } from './api/apiService';


function App() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);

  useEffect(() => {
    handleAuthentication();
  }, []);

  const handleAuthentication = async () => {
    // Attempt to retrieve the access token from local storage or URL
    const storedAccessToken = localStorage.getItem('accessToken');
    const urlAccessToken = new URLSearchParams(window.location.search).get('access_token');
    const accessToken = storedAccessToken ?? urlAccessToken;

    if (!accessToken) {
      setIsLoggedIn(false);
      return; // No token found, exit early
    }
    // Check the validity of the access token
    const isValidToken = await checkAccessToken(accessToken);
    setIsLoggedIn(isValidToken);

    if (isValidToken) {
      localStorage.setItem('accessToken', accessToken); // Save to local storage if valid
    } else {
      localStorage.removeItem('accessToken'); // Remove from local storage if invalid
    }
  };

  return (
    <div className="container-fluid" style={{ paddingTop: '60px' }}>
      <NavBar isLoggedIn={isLoggedIn} setIsLoggedIn={setIsLoggedIn}></NavBar>
      <Header></Header>
      <Dashboard></Dashboard>


      <ToastContainer
        position="top-right"
        autoClose={1500}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover

        style={{ paddingTop: '30px' }}
      />
    </div>
  );
}

export default App;
