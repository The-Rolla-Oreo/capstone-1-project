import { Container, Box, Typography, Button, Stack, Grid, Card, CardContent } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import GroupsIcon from '@mui/icons-material/Groups';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import AssignmentIcon from '@mui/icons-material/Assignment';
import LocalActivityIcon from '@mui/icons-material/LocalActivity';

export default function Landing() {
  const navigate = useNavigate();

  const features = [
    { icon: <GroupsIcon sx={{ fontSize: 48, color: 'primary.main' }} />, title: 'Group Management', description: 'Create groups and invite your roommates to coordinate together.' },
    { icon: <AssignmentIcon sx={{ fontSize: 48, color: 'primary.main' }} />, title: 'Chore Management', description: 'Organize and assign chores among group members easily.' },
    { icon: <CalendarMonthIcon sx={{ fontSize: 48, color: 'primary.main' }} />, title: 'Schedule Planning', description: 'Plan shared schedules and stay on top of deadlines.' },
    { icon: <LocalActivityIcon sx={{ fontSize: 48, color: 'primary.main' }} />, title: 'Activity Tracking', description: 'Track completed tasks and monitor group progress.' },
  ];

  return (
    <>
      {/* Hero Section */}
      <Box
        sx={(theme) => ({
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
          color: 'common.white',
          py: { xs: 8, md: 12 },
          textAlign: 'center',
        })}
      >
        <Container maxWidth="md">
          <Typography component="h1" variant="h2" gutterBottom sx={{ fontWeight: '700', mb: 2 }}>
            DormSpace - roommate coordination made simple
          </Typography>
          <Typography variant="h5" sx={{ mb: 4, opacity: 0.95 }}>
            Assign chores, share schedules, and keep your household running smoothly.
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
            <Button variant="contained" size="large" onClick={() => navigate('/signup')}>Get Started</Button>
            <Button variant="outlined" size="large" onClick={() => navigate('/login')} sx={{ borderColor: 'rgba(255,255,255,0.8)', color: 'common.white' }}>
              Sign In
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography component="h2" variant="h3" gutterBottom sx={{ textAlign: 'center', mb: 6, fontWeight: '700' }}>
          Why choose DormSpace?
        </Typography>

        <Grid container spacing={4} justifyContent="center">
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', textAlign: 'center', transition: '0.3s', '&:hover': { transform: 'translateY(-5px)', boxShadow: 6 } }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                  <Typography gutterBottom variant="h6" component="div" sx={{ fontWeight: '600' }}>{feature.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{feature.description}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Call to Action */}
      <Box sx={{ backgroundColor: 'background.paper', py: 8, textAlign: 'center' }}>
        <Container maxWidth="md">
          <Typography component="h2" variant="h4" gutterBottom sx={{ fontWeight: '700', mb: 2 }}>
            Ready to simplify roommate coordination?
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
            Create your group and start organizing today.
          </Typography>
          <Button variant="contained" size="large" onClick={() => navigate('/signup')}>Start Today</Button>
        </Container>
      </Box>
    </>
  );
}