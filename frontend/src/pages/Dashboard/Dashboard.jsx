import { useState, useEffect } from 'react';
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Card, CardContent, Button, Grid } from '@mui/material';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);



  const fetchUserDetails = useCallback(async () => {
    try {
      const endpoint = '/api/auth/my-details'
      const response = await fetch(endpoint, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Clear state and redirect
          setUser(null);
          setGroup(null);
          navigate('/login', { replace: true }); // replace: true prevents going back
          return;
        }
        throw new Error('Failed to fetch user details');
      }

      const data = await response.json();
      setUser(data);
    } catch (err) {
      setError(err.message);
      setUser(null);
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  const fetchGroupDetails = useCallback(async () => {
    try {
      const endpoint = '/api/groups/my-group'
      const response = await fetch(endpoint, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setGroup(data);
      } else if (response.status === 404) {
        // User not in a group yet - this is okay
        setGroup(null);
      }
    } catch (err) {
      console.error('Error fetching group:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch user details on component mount
  useEffect(() => {
    fetchUserDetails();
    fetchGroupDetails();
  }, [fetchUserDetails, fetchGroupDetails]);

  const handleLogout = async () => {
    try {
      const endpoint = '/api/auth/logout'
      await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      // Always clear state and navigate, even if logout fails
      setUser(null);
      setGroup(null);
      navigate('/login', { replace: true }); // This prevents back button navigation
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ padding: 4 }}>
      {/* Welcome Section */}
      <Typography variant="h3" gutterBottom>
        Welcome, {user?.username}!
      </Typography>

      <Grid container spacing={3}>
        {/* User Profile Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Profile Details
              </Typography>
              <Typography variant="body1">
                <strong>Username:</strong> {user?.username}
              </Typography>
              <Typography variant="body1">
                <strong>Email:</strong> {user?.email}
              </Typography>
              <Typography variant="body1">
                <strong>Full Name:</strong> {user?.full_name}
              </Typography>
              <Typography variant="body1">
                <strong>Email Verified:</strong> {user?.email_verified ? 'Yes' : 'No'}
              </Typography>
              <Button 
                variant="contained" 
                sx={{ mt: 2 }}
                onClick={() => navigate('/settings')}
              >
                Edit Profile
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Group Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Household Group
              </Typography>
              {group ? (
                <>
                  <Typography variant="body1">
                    <strong>Group Name:</strong> {group.group_name}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Admin:</strong> {group.group_admin_username}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Members:</strong> {group.users_in_group?.length || 0}
                  </Typography>
                  <Button 
                    variant="contained" 
                    sx={{ mt: 2, mr: 1 }}
                    onClick={() => navigate('/group-details')}
                  >
                    View Group
                  </Button>
                  <Button 
                    variant="outlined" 
                    color="error"
                    sx={{ mt: 2 }}
                    onClick={() => navigate('/leave-group')}
                  >
                    Leave Group
                  </Button>
                </>
              ) : (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    You are not part of any group yet.
                  </Typography>
                  <Button 
                    variant="contained" 
                    sx={{ mr: 1 }}
                    onClick={() => navigate('/create-group')}
                  >
                    Create Group
                  </Button>
                  <Button 
                    variant="outlined"
                    onClick={() => navigate('/join-group')}
                  >
                    Join Group
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button variant="contained">Add Expense</Button>
                <Button variant="contained">View Expenses</Button>
                <Button variant="contained">Generate Report</Button>
                <Button variant="outlined" color="error" onClick={handleLogout}>
                  Logout
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;