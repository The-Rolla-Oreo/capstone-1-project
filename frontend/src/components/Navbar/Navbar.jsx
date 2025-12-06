import { AppBar, Container, Toolbar, Button, Box } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export default function Navbar({ isAuthenticated }) {
  const navigate = useNavigate()
  return (
    <AppBar position="sticky" color="transparent" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ py: 1 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Button onClick={() => navigate('/')} sx={{ color: 'text.primary', textTransform: 'none', fontWeight: 700, fontSize: 18 }}>
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
              <Button color="inherit" onClick={() => navigate('/login')} sx={{ textTransform: 'none' }}>Login</Button>
              <Button variant="contained" onClick={() => navigate('/signup')} sx={{ ml: 1 }}>Sign Up</Button>
            </>
          )}
        </Toolbar>
      </Container>
    </AppBar>
  )
}