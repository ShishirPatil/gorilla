import 'bootstrap/dist/css/bootstrap.min.css';
// Components
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import NavBar from './components/NavBar';
import './App.css';

function App() {
  return (
    <div className="container-fluid" style={{ paddingTop: '60px' }}>
      <NavBar></NavBar>
      <Header></Header>
      <Dashboard></Dashboard>
    </div>
  );
}

export default App;
