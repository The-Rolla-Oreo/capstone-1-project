import { createTheme } from '@mui/material/styles'
import { lighten } from '@mui/material'

const PRIMARY = '#2563eb'
const SECONDARY = '#06b6d4'
const BG_DEFAULT = '#071023'
const BG_PAPER = '#0f1724'
const TEXT_PRIMARY = '#E6EEF8'

let theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: PRIMARY },
    secondary: { main: SECONDARY },
    background: { default: BG_DEFAULT, paper: BG_PAPER },
    text: { primary: TEXT_PRIMARY, secondary: lighten(TEXT_PRIMARY, 0.22) },
  },
  typography: {
    fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: BG_DEFAULT,
          color: TEXT_PRIMARY,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
          boxShadow: 'none',
          borderBottom: '1px solid rgba(255,255,255,0.04)',
          backdropFilter: 'blur(6px)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 10 },
        containedPrimary: {
          backgroundImage: `linear-gradient(90deg, ${PRIMARY}, ${SECONDARY})`,
          color: '#fff',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundImage: 'linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01))',
          border: '1px solid rgba(255,255,255,0.03)',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: lighten(PRIMARY, 0.18),
          color: '#fff',
          borderRadius: 6,
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          backgroundColor: BG_PAPER,
          color: TEXT_PRIMARY,
          border: '1px solid rgba(255,255,255,0.03)',
        },
      },
    },
  },
})

export default theme