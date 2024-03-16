import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';

// Components
import Header from '../components/Header';
import Dashboard from '../components/Dashboard';


function index() {
  return (
    <div className="container-fluid">
      <Header></Header>
      <Dashboard></Dashboard>
    </div>

  );
}

export default index;