import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Layout from './components/Layout.jsx';
import Landing from './pages/Landing/Landing.jsx';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  return (
    <Router>
      <Layout isAuthenticated={isAuthenticated}>
        <Routes>
          <Route path="/" element={<Landing />} />
          {/* Add more routes here for signup, login, dashboard, etc. */}
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
