import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Container, Table, Card, Spinner, Button, Form } from 'react-bootstrap';

const MonitoringDashboard = () => {
  const [streamData, setStreamData] = useState([]);
  const [errorSuccessStats, setErrorSuccessStats] = useState({});
  const [failingAgents, setFailingAgents] = useState([]);
  const [totalRatings, setTotalRatings] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterErrors, setFilterErrors] = useState(false);
  const [passcode, setPasscode] = useState('');
  const [authenticated, setAuthenticated] = useState(false);

  const apiUrl = 'https://agent-arena.vercel.app/api/monitoring';

  // Function to check the passcode locally (not sent to backend)
  const handlePasscodeSubmit = (e) => {
    e.preventDefault();
    const correctPasscode = process.env.REACT_APP_DASHBOARD_PASSCODE;

    if (passcode === correctPasscode) {
      setAuthenticated(true);
      fetchData(); // Fetch data after successful passcode entry
    } else {
      alert('Invalid passcode');
    }
  };

  // Fetch monitoring data after authentication
  const fetchData = async () => {
    try {
      const [statsRes, agentsRes, ratingsRes] = await Promise.all([
        axios.get(`${apiUrl}/stats`),
        axios.get(`${apiUrl}/failing-agents`),
        axios.get(`${apiUrl}/total-ratings`),
      ]);

      setErrorSuccessStats(statsRes.data);
      setFailingAgents(agentsRes.data);
      setTotalRatings(ratingsRes.data.totalRatings);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data', error);
    }
  };

  // Streaming executed code and errors after authentication
  useEffect(() => {
    if (authenticated) {
      const eventSource = new EventSource(`${apiUrl}/stream-data`);

      eventSource.onmessage = (event) => {
        setStreamData((prevData) => [JSON.parse(event.data), ...prevData]); // Most recent at the top
      };

      eventSource.onerror = (error) => {
        console.error('Error streaming data', error);
        eventSource.close();
      };

      return () => {
        eventSource.close();
      };
    }
  }, [authenticated]);

  if (!authenticated) {
    return (
      <Container>
        <h2>Enter Dashboard Passcode</h2>
        <Form onSubmit={handlePasscodeSubmit}>
          <Form.Group>
            <Form.Control
              type="password"
              placeholder="Enter passcode"
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
            />
          </Form.Group>
          <Button type="submit">Submit</Button>
        </Form>
      </Container>
    );
  }

  if (loading) return <Spinner animation="border" />;

  const filteredData = filterErrors
    ? streamData.filter((execution) => !execution.isSuccess)
    : streamData;

  return (
    <Container>
      <h2>Monitoring Dashboard</h2>

      <Card className="mb-4">
        <Card.Body>
          <h4>Error/Success Rates (Last 30 Minutes)</h4>
          <p>Success Rate: {errorSuccessStats.successRate}%</p>
          <p>Fail Rate: {errorSuccessStats.failRate}%</p>
        </Card.Body>
      </Card>

      <Card className="mb-4">
        <Card.Body>
          <h4>Agents Failing the Most</h4>
          <ul>
            {failingAgents.map((agent) => (
              <li key={agent._id}>
                {agent.name} (Failures: {agent.failCount})
              </li>
            ))}
          </ul>
        </Card.Body>
      </Card>

      <Card className="mb-4">
        <Card.Body>
          <h4>Total Ratings</h4>
          <p>Total number of ratings: {totalRatings}</p>
        </Card.Body>
      </Card>

      <Card className="mb-4">
        <Card.Body>
          <h4>Real-time Execution Status</h4>
          <div className="table-responsive">
            <Button onClick={() => setFilterErrors(!filterErrors)}>
              {filterErrors ? 'Show All' : 'Show Errors Only'}
            </Button>
            <Table striped bordered hover>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Agent</th>
                  <th>Status</th>
                  <th>Output</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.slice(0, 50).map((execution, index) => (
                  <tr key={index}>
                    <td>{new Date(execution.timestamp).toLocaleString()}</td>
                    <td>{execution.agentId ? execution.agentId.name : 'Unknown Agent'}</td>
                    <td>{execution.isSuccess ? 'Success' : 'Error'}</td>
                    <td>{execution.output}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default MonitoringDashboard;
