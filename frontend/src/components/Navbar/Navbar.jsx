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
            <Button onClick={() => navigate('/')} className="logo-button" sx={{ fontSize: '22px', fontWeight: 'bold' }}>
              DormSpace
            </Button>
          </Box>

          {isAuthenticated ? (
            <>
              <Button color="inherit" onClick={() => navigate('/dashboard')} sx={{ fontSize: '16px' }}>Dashboard</Button>
              <Button color="inherit" onClick={() => navigate('/profile')} sx={{ fontSize: '16px' }}>Profile</Button>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/login')} className="login-btn" sx={{ fontSize: '16px' }}>
                Login
              </Button>
              <Button variant="contained" onClick={() => navigate('/signup')} className="signup-btn" sx={{ fontSize: '16px' }}>
                Sign Up
              </Button>
            </>
          )}
        </Toolbar>
      </Container>
    </AppBar>
  );
}
