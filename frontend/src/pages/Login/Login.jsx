import { useState } from 'react'
import { Container, Box, Typography, TextField, Button, Stack, Alert, Snackbar } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [successOpen, setSuccessOpen] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const endpoint = '/backend/auth/login'

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }).toString(),
        credentials: 'include' // if backend uses cookies/auth
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Login failed')
      }

      const data = await res.json().catch(() => ({}))
      // store token if provided
      if (data.access_token) {
        try {
          localStorage.setItem('auth_token', data.access_token)
        } catch (storageErr) {
          // localStorage may fail if storage quota is exceeded or in private/incognito mode
          console.warn('Failed to store token in localStorage:', storageErr)
          // Token is still in the httpOnly cookie, so login still works
        }
      }

      setSuccessOpen(true)
      setTimeout(() => navigate('/'), 800)
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
          Sign in to DormSpace
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Enter your username and password to continue.
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
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
            />

            {error && <Alert severity="error">{error}</Alert>}

            <Button type="submit" variant="contained" size="large" disabled={submitting}>
              {submitting ? 'Signing in…' : 'Sign In'}
            </Button>

            <Button variant="text" onClick={() => navigate('/signup')}>
              Don't have an account? Sign up
            </Button>
          </Stack>
        </Box>
      </Box>

      <Snackbar open={successOpen} autoHideDuration={1600} onClose={() => setSuccessOpen(false)}>
        <Alert severity="success" sx={{ width: '100%' }}>
          Signed in — redirecting
        </Alert>
      </Snackbar>
    </Container>
  )
}
