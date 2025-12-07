import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Layout from './components/Layout.jsx';
import Landing from './pages/Landing/Landing.jsx';
import Signup from './pages/Signup/Signup.jsx';
import Login from './pages/Login/Login.jsx';
import EmailVerification from './pages/EmailVerification/EmailVerification.jsx'
import Dashboard from './pages/Dashboard/Dashboard.jsx';
import JoinGroup from './pages/JoinGroup/JoinGroup.jsx';
import './App.css';

function App() {
  const [isAuthenticated, _setIsAuthenticated] = useState(false);

  return (
    <Router>
      <Layout isAuthenticated={isAuthenticated}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route path="/auth/verify-email" element={<EmailVerification />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/groups/join-group" element={<JoinGroup />} />
          {/* Add more routes here for dashboard, etc. */}
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
