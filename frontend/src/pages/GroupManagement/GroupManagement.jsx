import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RRule } from 'rrule';
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
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Checkbox,
  FormGroup,
  Divider,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';

export default function GroupManagement() {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Data states
  const [group, setGroup] = useState(null);
  const [groupMembers, setGroupMembers] = useState([]);
  const [chores, setChores] = useState([]);
  const [recurringChores, setRecurringChores] = useState([]);

  // Dialog states
  const [createChoreOpen, setCreateChoreOpen] = useState(false);
  const [createRecurringOpen, setCreateRecurringOpen] = useState(false);
  const [editRecurringOpen, setEditRecurringOpen] = useState(false);

  // Form states for regular chore
  const [choreName, setChoreName] = useState('');
  const [choreDescription, setChoreDescription] = useState('');
  const [assignedUsername, setAssignedUsername] = useState('');

  // Form states for recurring chore
  const [recurringChoreName, setRecurringChoreName] = useState('');
  const [recurringChoreDescription, setRecurringChoreDescription] = useState('');
  const [recurringAssignedUsernames, setRecurringAssignedUsernames] = useState([]);
  const [frequency, setFrequency] = useState('WEEKLY');
  const [interval, setInterval] = useState(1);
  const [selectedDays, setSelectedDays] = useState([]);
  const [startDate, setStartDate] = useState('');

  // Edit recurring chore states
  const [editingRecurringChore, setEditingRecurringChore] = useState(null);
  const [editRecurringName, setEditRecurringName] = useState('');
  const [editRecurringDescription, setEditRecurringDescription] = useState('');
  const [editRecurringActive, setEditRecurringActive] = useState(true);

  // Fetch group details
  const fetchGroupDetails = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/groups/my-group`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setGroup(data);
        
        // Fetch usernames for group members
        if (data.users_in_group && data.users_in_group.length > 0) {
          const members = data.users_in_group.map(userId => ({
            id: userId,
            username: data.users_in_group_usernames?.[data.users_in_group.indexOf(userId)] || 'Unknown'
          }));
          setGroupMembers(members);
        }
      } else if (response.status === 401) {
        navigate('/login');
      } else {
        setError('Not in a group');
        setTimeout(() => navigate('/dashboard'), 2000);
      }
    } catch (err) {
      console.error("Error details:", err);
      setError('Failed to load group details');
    }
  }, [navigate]);

  // Fetch chores
  const fetchChores = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/chores`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setChores(data);
      }
    } catch (err) {
      console.error('Failed to fetch chores:', err);
    }
  }, []);

  // Fetch recurring chores
  const fetchRecurringChores = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/recurring-chores/`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setRecurringChores(data);
      }
    } catch (err) {
      console.error('Failed to fetch recurring chores:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGroupDetails();
    fetchChores();
    fetchRecurringChores();
  }, [fetchGroupDetails, fetchChores, fetchRecurringChores]);

  // Handle create chore
  const handleCreateChore = async () => {
    setError('');
    setSuccess('');

    if (!choreName || !choreDescription) {
      setError('Please fill in all fields');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('chore_name', choreName);
      formData.append('chore_description', choreDescription);
      if (assignedUsername) {
        formData.append('assigned_username', assignedUsername);
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/create-chore`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create chore');
      }

      setSuccess('Chore created successfully');
      setChoreName('');
      setChoreDescription('');
      setAssignedUsername('');
      setCreateChoreOpen(false);
      fetchChores();
    } catch (err) {
      setError(err.message);
    }
  };

  // Handle complete chore
  const handleCompleteChore = async (choreId) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/complete-chore/${choreId}`, {
        method: 'POST',
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to complete chore');
      }

      setSuccess('Chore marked as complete');
      fetchChores();
    } catch (err) {
      setError(err.message);
    }
  };

  // Handle delete chore
  const handleDeleteChore = async (choreId) => {
    if (!confirm('Are you sure you want to delete this chore?')) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/delete-chore/${choreId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to delete chore');
      }

      setSuccess('Chore deleted successfully');
      fetchChores();
    } catch (err) {
      setError(err.message);
    }
  };

  // Build RRULE string
  const buildRRule = () => {
    let rrule = `FREQ=${frequency}`;
    
    if (interval > 1) {
      rrule += `;INTERVAL=${interval}`;
    }
    
    if (frequency === 'WEEKLY' && selectedDays.length > 0) {
      const days = selectedDays.join(',');
      rrule += `;BYDAY=${days}`;
    }
    
    return rrule;
  };

  // Handle create recurring chore
  const handleCreateRecurringChore = async () => {
    setError('');
    setSuccess('');

    if (!recurringChoreName || !recurringChoreDescription || recurringAssignedUsernames.length === 0 || !startDate) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('chore_name', recurringChoreName);
      formData.append('chore_description', recurringChoreDescription);
      
      // Add each username separately
      recurringAssignedUsernames.forEach(username => {
        formData.append('assigned_usernames', username);
      });
      
      formData.append('rrule_str', buildRRule());
      formData.append('start_date_str', new Date(startDate).toISOString());

      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/recurring-chores/`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create recurring chore');
      }

      setSuccess('Recurring chore created successfully');
      setRecurringChoreName('');
      setRecurringChoreDescription('');
      setRecurringAssignedUsernames([]);
      setFrequency('WEEKLY');
      setInterval(1);
      setSelectedDays([]);
      setStartDate('');
      setCreateRecurringOpen(false);
      fetchRecurringChores();
    } catch (err) {
      setError(err.message);
    }
  };

  // Handle edit recurring chore
  const handleEditRecurringChore = async () => {
    setError('');
    setSuccess('');

    try {
      const formData = new FormData();
      if (editRecurringName) formData.append('chore_name', editRecurringName);
      if (editRecurringDescription) formData.append('chore_description', editRecurringDescription);
      formData.append('is_active', editRecurringActive);

      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/recurring-chores/${editingRecurringChore._id}`, {
        method: 'PUT',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update recurring chore');
      }

      setSuccess('Recurring chore updated successfully');
      setEditRecurringOpen(false);
      setEditingRecurringChore(null);
      fetchRecurringChores();
    } catch (err) {
      setError(err.message);
    }
  };

  // Handle delete recurring chore
  const handleDeleteRecurringChore = async (recurringChoreId) => {
    if (!confirm('Are you sure you want to delete this recurring chore? All associated chores will be deleted.')) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/chores/recurring-chores/${recurringChoreId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to delete recurring chore');
      }

      setSuccess('Recurring chore deleted successfully');
      fetchRecurringChores();
      fetchChores(); // Refresh chores as they might be affected
    } catch (err) {
      setError(err.message);
    }
  };

  // Open edit dialog
  const openEditDialog = (recurringChore) => {
    setEditingRecurringChore(recurringChore);
    setEditRecurringName(recurringChore.chore_name);
    setEditRecurringDescription(recurringChore.chore_description);
    setEditRecurringActive(recurringChore.is_active);
    setEditRecurringOpen(true);
  };

  // Get username by user ID
  const getUsernameById = (userId) => {
    const member = groupMembers.find(m => m.id === userId);
    return member ? member.username : 'Unknown';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ padding: 4 }}>
      {/* Success/Error Messages */}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h3">
          {group?.group_name} - Chore Management
        </Typography>
        <Button variant="outlined" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Chores" />
          <Tab label="Recurring Chores" />
          <Tab label="Group Members" />
        </Tabs>
      </Box>

      {/* Tab 0: Chores */}
      {tabValue === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5">All Chores</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateChoreOpen(true)}
            >
              Create Chore
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Chore Name</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {chores.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No chores yet. Create your first chore!
                    </TableCell>
                  </TableRow>
                ) : (
                  chores.map((chore) => (
                    <TableRow key={chore._id}>
                      <TableCell>{chore.chore_name}</TableCell>
                      <TableCell>{chore.chore_description}</TableCell>
                      <TableCell>{getUsernameById(chore.assigned_user_id)}</TableCell>
                      <TableCell>
                        {chore.is_completed ? (
                          <Chip label="Completed" color="success" size="small" />
                        ) : (
                          <Chip label="Pending" color="warning" size="small" />
                        )}
                      </TableCell>
                      <TableCell>
                        {new Date(chore.created_at + 'Z').toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {!chore.is_completed && (
                          <IconButton
                            color="success"
                            onClick={() => handleCompleteChore(chore._id)}
                            title="Mark as complete"
                          >
                            <CheckCircleIcon />
                          </IconButton>
                        )}
                        <IconButton
                          color="error"
                          onClick={() => handleDeleteChore(chore._id)}
                          title="Delete chore"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Tab 1: Recurring Chores */}
      {tabValue === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5">Recurring Chore Schedules</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateRecurringOpen(true)}
            >
              Create Recurring Chore
            </Button>
          </Box>

          <Grid container spacing={3}>
            {recurringChores.length === 0 ? (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography align="center">
                      No recurring chores yet. Create a schedule to automate chores!
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ) : (
              recurringChores.map((rc) => (
                <Grid item xs={12} md={6} key={rc._id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="h6">{rc.chore_name}</Typography>
                        <Box>
                          <IconButton
                            size="small"
                            onClick={() => openEditDialog(rc)}
                            title="Edit"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteRecurringChore(rc._id)}
                            title="Delete"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {rc.chore_description}
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="body2">
                        <strong>Schedule:</strong> {RRule.fromString(rc.rrule).toText()}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Next Due:</strong>{' '}
                        {new Date(rc.next_due_date + 'Z').toLocaleString()}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Assigned Users:</strong>{' '}
                        {rc.assigned_user_ids.map(getUsernameById).join(', ')}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip
                          label={rc.is_active ? 'Active' : 'Inactive'}
                          color={rc.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </Box>
      )}

      {/* Tab 2: Group Members */}
      {tabValue === 2 && (
        <Box>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Group Members
          </Typography>
          <Card>
            <CardContent>
              <Typography variant="body1" sx={{ mb: 2 }}>
                <strong>Group Admin:</strong> {group?.group_admin_username}
              </Typography>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Members ({groupMembers.length})
              </Typography>
              {groupMembers.map((member, index) => (
                <Chip key={index} label={member.username} sx={{ mr: 1, mb: 1 }} />
              ))}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Create Chore Dialog */}
      <Dialog open={createChoreOpen} onClose={() => setCreateChoreOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Chore</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Chore Name"
            fullWidth
            variant="outlined"
            value={choreName}
            onChange={(e) => setChoreName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={choreDescription}
            onChange={(e) => setChoreDescription(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth variant="outlined">
            <InputLabel>Assign To (Optional)</InputLabel>
            <Select
              value={assignedUsername}
              onChange={(e) => setAssignedUsername(e.target.value)}
              label="Assign To (Optional)"
            >
              <MenuItem value="">
                <em>Assign to me</em>
              </MenuItem>
              {groupMembers.map((member) => (
                <MenuItem key={member.id} value={member.username}>
                  {member.username}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateChoreOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateChore} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Recurring Chore Dialog */}
      <Dialog open={createRecurringOpen} onClose={() => setCreateRecurringOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Recurring Chore Schedule</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Chore Name"
            fullWidth
            variant="outlined"
            value={recurringChoreName}
            onChange={(e) => setRecurringChoreName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={recurringChoreDescription}
            onChange={(e) => setRecurringChoreDescription(e.target.value)}
            sx={{ mb: 2 }}
          />

          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Assign to (select one or more for rotation):
          </Typography>
          <FormGroup sx={{ mb: 2 }}>
            {groupMembers.map((member) => (
              <FormControlLabel
                key={member.id}
                control={
                  <Checkbox
                    checked={recurringAssignedUsernames.includes(member.username)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRecurringAssignedUsernames([...recurringAssignedUsernames, member.username]);
                      } else {
                        setRecurringAssignedUsernames(
                          recurringAssignedUsernames.filter((u) => u !== member.username)
                        );
                      }
                    }}
                  />
                }
                label={member.username}
              />
            ))}
          </FormGroup>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Frequency</InputLabel>
            <Select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              label="Frequency"
            >
              <MenuItem value="DAILY">Daily</MenuItem>
              <MenuItem value="WEEKLY">Weekly</MenuItem>
              <MenuItem value="MONTHLY">Monthly</MenuItem>
            </Select>
          </FormControl>

          <TextField
            margin="dense"
            label="Repeat Every (interval)"
            type="number"
            fullWidth
            variant="outlined"
            value={interval}
            onChange={(e) => setInterval(parseInt(e.target.value) || 1)}
            inputProps={{ min: 1 }}
            sx={{ mb: 2 }}
            helperText={`Every ${interval} ${frequency.toLowerCase()}`}
          />

          {frequency === 'WEEKLY' && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Select Days:
              </Typography>
              <FormGroup row>
                {['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'].map((day) => (
                  <FormControlLabel
                    key={day}
                    control={
                      <Checkbox
                        checked={selectedDays.includes(day)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDays([...selectedDays, day]);
                          } else {
                            setSelectedDays(selectedDays.filter((d) => d !== day));
                          }
                        }}
                      />
                    }
                    label={day}
                  />
                ))}
              </FormGroup>
            </Box>
          )}

          <TextField
            margin="dense"
            label="Start Date"
            type="datetime-local"
            fullWidth
            variant="outlined"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateRecurringOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateRecurringChore} variant="contained">
            Create Schedule
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Recurring Chore Dialog */}
      <Dialog open={editRecurringOpen} onClose={() => setEditRecurringOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Recurring Chore</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Chore Name"
            fullWidth
            variant="outlined"
            value={editRecurringName}
            onChange={(e) => setEditRecurringName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={editRecurringDescription}
            onChange={(e) => setEditRecurringDescription(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={editRecurringActive}
                onChange={(e) => setEditRecurringActive(e.target.checked)}
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditRecurringOpen(false)}>Cancel</Button>
          <Button onClick={handleEditRecurringChore} variant="contained">
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
