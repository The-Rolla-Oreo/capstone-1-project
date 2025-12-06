import { AppBar, Container, Toolbar, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LogoutIcon from '@mui/icons-material/Logout';

export default function Navbar({ isAuthenticated }) {
  const navigate = useNavigate();

  return (
    <AppBar position="static" sx={{ width: '100%' }}>
      <Container maxWidth={false} disableGutters>
        <Toolbar disableGutters sx={{ px: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Button color="inherit" onClick={() => navigate('/')} sx={{ textTransform: 'none', fontSize: '1.25rem', fontWeight: 'bold' }}>
              RoommateHub
            </Button>
          </Box>
          
          {isAuthenticated ? (
            <>
              <Button color="inherit" onClick={() => navigate('/dashboard')} sx={{ mx: 1 }}>
                Dashboard
              </Button>
              <Button color="inherit" onClick={() => navigate('/profile')} sx={{ mx: 1 }}>
                Profile
              </Button>
              <Button 
                color="inherit" 
                onClick={() => {
                  // Handle logout
                  navigate('/');
                }}
                endIcon={<LogoutIcon />}
                sx={{ mx: 1 }}
              >
                Logout
              </Button>
            </>
          ) : (
            <>
              <Button color="inherit" onClick={() => navigate('/login')} sx={{ mx: 1, textTransform: 'none' }}>
                Login
              </Button>
              <Button 
                variant="contained" 
                onClick={() => navigate('/signup')}
                sx={{ mx: 1, backgroundColor: 'white', color: 'primary.main', fontWeight: 'bold' }}
              >
                Sign Up
              </Button>
            </>
          )}
        </Toolbar>
      </Container>
    </AppBar>
  );
}