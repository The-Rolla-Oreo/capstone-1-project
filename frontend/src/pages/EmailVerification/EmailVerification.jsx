import { useEffect, useState, useRef } from 'react'
import { Container, Box, Typography, CircularProgress, Alert, Button } from '@mui/material'
import { useNavigate, useSearchParams } from 'react-router-dom'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'

export default function EmailVerification() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState('verifying') // 'verifying' | 'success' | 'error'
  const [message, setMessage] = useState('')
  const hasVerified = useRef(false) // Add this ref to track if verification already happened

  useEffect(() => {
    const verifyEmail = async () => {
      // Prevent double execution
      if (hasVerified.current) return
      hasVerified.current = true

      const token = searchParams.get('email_verification_token')
      
      if (!token) {
        setStatus('error')
        setMessage('Verification token is missing')
        return
      }

      try {
        const endpoint = `${import.meta.env.VITE_API_URL}/auth/verify-email`
        
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ email_verification_token: token }).toString(),
          credentials: 'include',
        })

        const data = await res.json().catch(() => ({}))

        if (!res.ok) {
          throw new Error(data.detail || 'Verification failed')
        }

        setStatus('success')
        setMessage(data.message || data.msg || 'Email verified successfully!')
        
        // Redirect to login after 3 seconds
        setTimeout(() => navigate('/login'), 3000)
      } catch (err) {
        setStatus('error')
        setMessage(err.message || 'Failed to verify email')
      }
    }

    verifyEmail()
  }, [searchParams, navigate])

  return (
    <Container maxWidth="sm" className="content-container">
      <Box sx={{ py: 8, textAlign: 'center' }}>
        {status === 'verifying' && (
          <>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Verifying your email...
            </Typography>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
              Email Verified!
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              {message}
            </Typography>
            <Alert severity="success" sx={{ mb: 3 }}>
              Redirecting to login...
            </Alert>
            <Button variant="contained" onClick={() => navigate('/login')}>
              Go to Login
            </Button>
          </>
        )}

        {status === 'error' && (
          <>
            <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
              Verification Failed
            </Typography>
            <Alert severity="error" sx={{ mb: 3 }}>
              {message}
            </Alert>
            <Button variant="contained" onClick={() => navigate('/login')}>
              Go to Login
            </Button>
          </>
        )}
      </Box>
    </Container>
  )
}