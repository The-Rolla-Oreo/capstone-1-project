import { useEffect, useState, useRef } from 'react'
import { Container, Box, Typography, CircularProgress, Alert, Button } from '@mui/material'
import { useNavigate, useSearchParams } from 'react-router-dom'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import apiClient from '../../apiClient'

export default function JoinGroup() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState('joining') // 'joining' | 'success' | 'error'
  const [message, setMessage] = useState('')
  const [groupName, setGroupName] = useState('')
  const hasJoined = useRef(false)

  useEffect(() => {
    const joinGroup = async () => {
      // Prevent double execution
      if (hasJoined.current) return
      hasJoined.current = true

      const token = searchParams.get('invite_token')
      
      if (!token) {
        setStatus('error')
        setMessage('Invite token is missing')
        return
      }

      try {
        const endpoint = '/groups/join-group'
        
        const formData = new FormData()
        formData.append('invite_token', token)

        const res = await apiClient(endpoint, {
          method: 'POST',
          body: formData,
        })

        const data = await res.json().catch(() => ({}))

        if (!res.ok) {
          throw new Error(data.detail || 'Failed to join group')
        }

        setStatus('success')
        setMessage(data.msg || 'Successfully joined the group!')
        
        // Optionally extract group name if returned from backend
        if (data.group_name) {
          setGroupName(data.group_name)
        }
        
        // Redirect to dashboard after 3 seconds
        setTimeout(() => navigate('/dashboard'), 3000)
      } catch (err) {
        setStatus('error')
        setMessage(err.message || 'Failed to join group')
      }
    }

    joinGroup()
  }, [searchParams, navigate])

  return (
    <Container maxWidth="sm" className="content-container">
      <Box sx={{ py: 8, textAlign: 'center' }}>
        {status === 'joining' && (
          <>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Joining group...
            </Typography>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
              Welcome to the Group!
            </Typography>
            {groupName && (
              <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                {groupName}
              </Typography>
            )}
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              {message}
            </Typography>
            <Alert severity="success" sx={{ mb: 3 }}>
              Redirecting to dashboard...
            </Alert>
            <Button variant="contained" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </Button>
          </>
        )}

        {status === 'error' && (
          <>
            <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
              Failed to Join Group
            </Typography>
            <Alert severity="error" sx={{ mb: 3 }}>
              {message}
            </Alert>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              You may already be in a group, or the invite link may be invalid or expired.
            </Typography>
            <Button variant="contained" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </Button>
          </>
        )}
      </Box>
    </Container>
  )
}