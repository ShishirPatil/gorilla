import 'bootstrap/dist/css/bootstrap.min.css';
// Components
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import NavBar from './components/NavBar';
import { ToastContainer } from 'react-toastify';
import './App.css';

function App() {
  return (
    <div className="container-fluid" style={{ paddingTop: '60px' }}>
      <NavBar></NavBar>
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
