import { Box, Container, Typography } from '@mui/material'
import "./Footer.css";

export default function Footer() {
  return (
    <Box component="footer" className="footer">
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          © {new Date().getFullYear()} DormSpace. All rights reserved.
        </Typography>
      </Container>
    </Box>
  );
}
