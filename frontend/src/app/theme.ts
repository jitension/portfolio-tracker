/**
 * Material-UI Theme Configuration
 * Based on MUI Dashboard Template - Dark Mode
 */
import { createTheme } from '@mui/material/styles';
import { colorSchemes, typography, shadows, shape } from './themePrimitives';
import { surfacesCustomizations, dataDisplayCustomizations } from './customizations';

const theme = createTheme({
  cssVariables: {
    colorSchemeSelector: 'data-mui-color-scheme',
    cssVarPrefix: 'portfolio',
  },
  colorSchemes, // Light & Dark mode support
  typography,
  shadows,
  shape,
  components: {
    ...surfacesCustomizations,
    ...dataDisplayCustomizations,
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: 'hsl(220, 20%, 42%) hsl(220, 30%, 6%)',
          '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
            width: 8,
            height: 8,
          },
          '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
            borderRadius: 8,
            backgroundColor: 'hsl(220, 20%, 42%)',
          },
          '&::-webkit-scrollbar-track, & *::-webkit-scrollbar-track': {
            backgroundColor: 'hsl(220, 30%, 6%)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

export default theme;
