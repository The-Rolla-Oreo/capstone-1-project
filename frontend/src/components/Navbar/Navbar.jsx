import { AppBar, Container, Toolbar, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import "./Navbar.css";

export default function Navbar({ isAuthenticated }) {
  const navigate = useNavigate();

  return (
    <AppBar position="sticky" color="transparent" elevation={0} className="navbar">
      <Container maxWidth={false}>
        <Toolbar disableGutters className="navbar-toolbar">
          <Box className="navbar-logo">
            <Button onClick={() => navigate('/')} className="logo-button">
              DormSpace
            </Button>
          </Box>

          {isAuthenticated ? (
            <>
              <Button color="inherit" onClick={() => navigate('/dashboard')}>Dashboard</Button>
              <Button color="inherit" onClick={() => navigate('/profile')}>Profile</Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/login')} className="login-btn">
                Login
              </Button>
              <Button variant="contained" onClick={() => navigate('/signup')} className="signup-btn">
                Sign Up
              </Button>
            </>
          )}
        </Toolbar>
      </Container>
    </AppBar>
  );
}
