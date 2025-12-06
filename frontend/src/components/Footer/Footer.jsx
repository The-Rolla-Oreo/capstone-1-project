import { Box, Container, Typography } from '@mui/material'

export default function Footer() {
  return (
    <Box component="footer" sx={{ mt: 8, py: 4, borderTop: '1px solid rgba(255,255,255,0.03)', backgroundColor: 'transparent' }}>
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          © {new Date().getFullYear()} DormSpace. All rights reserved.
        </Typography>
      </Container>
    </Box>
  )
}