import { Container, Box, Typography, Button, Stack, Grid, Card, CardContent } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import GroupsIcon from '@mui/icons-material/Groups';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import AssignmentIcon from '@mui/icons-material/Assignment';
import LocalActivityIcon from '@mui/icons-material/LocalActivity';

import "./Landing.css";

export default function Landing() {
  const navigate = useNavigate();

  const features = [
    { icon: <GroupsIcon className="feature-icon" />, title: 'Group Management', description: 'Create groups and invite your roommates to coordinate together.' },
    { icon: <AssignmentIcon className="feature-icon" />, title: 'Chore Management', description: 'Organize and assign chores among group members easily.' },
    { icon: <CalendarMonthIcon className="feature-icon" />, title: 'Schedule Planning', description: 'Plan shared schedules and stay on top of deadlines.' },
    { icon: <LocalActivityIcon className="feature-icon" />, title: 'Activity Tracking', description: 'Track completed tasks and monitor group progress.' },
  ];

  return (
    <>
      {/* Hero Section */}
      <Box className="hero">
        <Container maxWidth="md">
          <Box className="hero-gradient-box">
          <Typography component="h1" variant="h2" gutterBottom className="hero-title">
            DormSpace - roommate coordination made simple
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mb: 2 }} className="hero-subtitle">
            Assign chores, share schedules, and keep your household running smoothly.
          </Typography>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
            <Button variant="contained" size="large" onClick={() => navigate('/signup')}>
              Get Started
            </Button>

            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/login')}
              className="hero-signin"
            >
              Sign In
            </Button>
          </Stack>
          </Box>
        </Container>
      </Box>

      {/* Features Section */}
<Container maxWidth="lg" className="features-section">
  <Typography component="h2" variant="h3" gutterBottom className="features-title">
    Why choose DormSpace?
  </Typography>

  <div className="features-grid">
    {features.map((feature, index) => (
      <Card key={index} className="feature-card-fixed">
        <CardContent>
          <Box className="feature-icon-box">{feature.icon}</Box>

          <Typography gutterBottom variant="h6" className="feature-title">
            {feature.title}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            {feature.description}
          </Typography>
        </CardContent>
      </Card>
    ))}
  </div>
</Container>


      {/* Call to Action */}
      <Box className="cta-section">
        <Container maxWidth="md">
          <Typography component="h2" variant="h4" gutterBottom className="cta-title">
            Ready to simplify roommate coordination?
          </Typography>

          <Typography variant="body1" gutterBottom sx={{ mb: 2 }} className="cta-subtitle">
            Create your group and start organizing today.
          </Typography>

          <Button variant="contained" size="large" onClick={() => navigate('/signup')}>
            Start Today
          </Button>
        </Container>
      </Box>
    </>
  );
}
