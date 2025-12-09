import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert
} from '@mui/material';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Dialog states (removed joinGroupOpen)
  const [createGroupOpen, setCreateGroupOpen] = useState(false);
  const [leaveGroupOpen, setLeaveGroupOpen] = useState(false);
  const [inviteUserOpen, setInviteUserOpen] = useState(false);
  const [changeUsernameOpen, setChangeUsernameOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);

  // Form states (removed inviteToken)
  const [groupName, setGroupName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [actionError, setActionError] = useState('');
  const [actionSuccess, setActionSuccess] = useState('');

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

  // Create Group Handler
  const handleCreateGroup = async () => {
    setActionError('');
    setActionSuccess('');

    if (groupName.length < 5 || groupName.length > 35) {
      setActionError('Group name must be between 5 and 35 characters');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('group_name', groupName);

      const response = await fetch('/api/groups/create-group', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create group');
      }

      setActionSuccess(data.msg);
      setGroupName('');
      setCreateGroupOpen(false);
      
      // Refresh user and group details
      await fetchUserDetails();
      await fetchGroupDetails();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Leave Group Handler
  const handleLeaveGroup = async () => {
    setActionError('');
    setActionSuccess('');

    try {
      const response = await fetch('/api/groups/leave-group', {
        method: 'POST',
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to leave group');
      }

      setActionSuccess(data.msg);
      setLeaveGroupOpen(false);
      
      // Refresh user and group details
      await fetchUserDetails();
      await fetchGroupDetails();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Invite User Handler
  const handleInviteUser = async () => {
    setActionError('');
    setActionSuccess('');

    // Basic email validation
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!inviteEmail || !emailRegex.test(inviteEmail)) {
      setActionError('Please enter a valid email address');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('email', inviteEmail);

      const response = await fetch('/api/groups/invite-user', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send invite');
      }

      setActionSuccess(data.msg);
      setInviteEmail('');
      setInviteUserOpen(false);
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Change Username Handler
  const handleChangeUsername = async () => {
    setActionError('');
    setActionSuccess('');

    if (newUsername.length < 5 || newUsername.length > 35) {
      setActionError('Username must be between 5 and 35 characters');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('new_username', newUsername);

      const response = await fetch('/api/auth/change-username', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to change username');
      }

      setActionSuccess(data.msg);
      setNewUsername('');
      setChangeUsernameOpen(false);
      
      // Refresh user details to show new username
      await fetchUserDetails();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Change Password Handler
  const handleChangePassword = async () => {
    setActionError('');
    setActionSuccess('');

    if (newPassword.length < 15) {
      setActionError('New password must be at least 15 characters');
      return;
    }

    if (!oldPassword) {
      setActionError('Please enter your current password');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('old_password', oldPassword);
      formData.append('new_password', newPassword);

      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to change password');
      }

      setActionSuccess(data.msg);
      setOldPassword('');
      setNewPassword('');
      setChangePasswordOpen(false);
    } catch (err) {
      setActionError(err.message);
    }
  };

  return (
    <Box sx={{ padding: 4 }}>
      {/* Success/Error Messages */}
      {actionSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setActionSuccess('')}>
          {actionSuccess}
        </Alert>
      )}
      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setActionError('')}>
          {actionError}
        </Alert>
      )}

      {/* Welcome Section */}
      <Typography variant="h3" gutterBottom>
        Welcome, {user?.username}!
      </Typography>

      <Grid container spacing={3} justifyContent="center">
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
              <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
                <Button 
                  variant="contained" 
                  onClick={() => setChangeUsernameOpen(true)}
                >
                  Change Username
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => setChangePasswordOpen(true)}
                >
                  Change Password
                </Button>
              </Box>
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
                    variant="contained" 
                    color="primary"
                    sx={{ mt: 2, mr: 1 }}
                    onClick={() => setInviteUserOpen(true)}
                  >
                    Invite User
                  </Button>
                  <Button 
                    variant="outlined" 
                    color="error"
                    sx={{ mt: 2 }}
                    onClick={() => setLeaveGroupOpen(true)}
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
                    onClick={() => setCreateGroupOpen(true)}
                  >
                    Create Group
                  </Button>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    To join a group, click the invite link sent to your email.
                  </Typography>
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
                <Button variant="outlined" color="error" onClick={handleLogout}>
                  Logout
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Create Group Dialog */}
      <Dialog open={createGroupOpen} onClose={() => setCreateGroupOpen(false)}>
        <DialogTitle>Create a New Group</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Group Name"
            type="text"
            fullWidth
            variant="outlined"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            helperText="Group name must be between 5 and 35 characters"
            inputProps={{ minLength: 5, maxLength: 35 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateGroupOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateGroup} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Leave Group Confirmation Dialog */}
      <Dialog open={leaveGroupOpen} onClose={() => setLeaveGroupOpen(false)}>
        <DialogTitle>Leave Group</DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Are you sure you want to leave {group?.group_name}?
          </Typography>
          {group?.group_admin_id === user?.id && (
            <Typography variant="body2" color="warning.main">
              You are the admin. Another member will be promoted to admin if you leave.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLeaveGroupOpen(false)}>Cancel</Button>
          <Button onClick={handleLeaveGroup} variant="contained" color="error">
            Leave Group
          </Button>
        </DialogActions>
      </Dialog>

      {/* Invite User Dialog */}
      <Dialog open={inviteUserOpen} onClose={() => setInviteUserOpen(false)}>
        <DialogTitle>Invite User to Group</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email Address"
            type="email"
            fullWidth
            variant="outlined"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            helperText="Enter the email address of the user you want to invite"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteUserOpen(false)}>Cancel</Button>
          <Button onClick={handleInviteUser} variant="contained">
            Send Invite
          </Button>
        </DialogActions>
      </Dialog>

      {/* Change Username Dialog */}
      <Dialog open={changeUsernameOpen} onClose={() => setChangeUsernameOpen(false)}>
        <DialogTitle>Change Username</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="New Username"
            type="text"
            fullWidth
            variant="outlined"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            helperText="Username must be between 5 and 35 characters"
            inputProps={{ minLength: 5, maxLength: 35 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangeUsernameOpen(false)}>Cancel</Button>
          <Button onClick={handleChangeUsername} variant="contained">
            Change Username
          </Button>
        </DialogActions>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={changePasswordOpen} onClose={() => setChangePasswordOpen(false)}>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Current Password"
            type="password"
            fullWidth
            variant="outlined"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="New Password"
            type="password"
            fullWidth
            variant="outlined"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            helperText="Password must be at least 15 characters"
            inputProps={{ minLength: 15 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangePasswordOpen(false)}>Cancel</Button>
          <Button onClick={handleChangePassword} variant="contained">
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;