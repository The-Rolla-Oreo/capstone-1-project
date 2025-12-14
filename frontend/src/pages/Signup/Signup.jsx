import { useState } from 'react'
import { Container, Box, Typography, TextField, Button, Stack, Alert, Snackbar } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export default function Signup() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [successOpen, setSuccessOpen] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const endpoint = '/api/auth/register'
      
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, full_name: fullName, email, password }).toString(),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        // Handle both string and array of validation errors
        let errorMessage = 'Signup failed'
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail
          } else if (Array.isArray(data.detail)) {
            // Extract error messages from FastAPI validation error format and make them more user-friendly
            errorMessage = data.detail.map(err => {
              const field = err.loc ? err.loc[err.loc.length - 1] : 'Field'
              const fieldName = field === 'full_name' ? 'Full Name' : 
                                field.charAt(0).toUpperCase() + field.slice(1)
              
              if (err.msg) {
                // Customize common validation messages
                if (err.msg.includes('at least 5 characters')) {
                  return `${fieldName} must be at least 5 characters`
                } else if (err.msg.includes('at least 15 characters')) {
                  return `${fieldName} must be at least 15 characters`
                } else if (err.msg.includes('match pattern')) {
                  return `${fieldName} must be a valid email address`
                } else {
                  return `${fieldName}: ${err.msg}`
                }
              }
              return err.message || JSON.stringify(err)
            }).join('; ')
          } else if (typeof data.detail === 'object') {
            errorMessage = JSON.stringify(data.detail)
          }
        }
        throw new Error(errorMessage)
      }

      setSuccessOpen(true)
      // after short delay navigate to login
      setTimeout(() => navigate('/login'), 1200)
    } catch (err) {
      setError(err.message || String(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Container maxWidth="sm" className="content-container">
      <Box sx={{ py: 6, textAlign: 'center' }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
          Create your DormSpace account
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Sign up to create or join a household and start coordinating with roommates.
        </Typography>

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Stack spacing={2}>
            <TextField
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
            />

            {error && <Alert severity="error">{error}</Alert>}

            <Button type="submit" variant="contained" size="large" disabled={submitting}>
              {submitting ? 'Creating account…' : 'Create Account'}
            </Button>

            <Button variant="text" onClick={() => navigate('/login')}>
              Already have an account? Sign in
            </Button>
          </Stack>
        </Box>
      </Box>

      <Snackbar open={successOpen} autoHideDuration={2000} onClose={() => setSuccessOpen(false)}>
        <Alert severity="success" sx={{ width: '100%' }}>
          Account created — redirecting to login
        </Alert>
      </Snackbar>
    </Container>
  )
}
