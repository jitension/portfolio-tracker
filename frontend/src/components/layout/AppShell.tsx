/**
 * AppShell Component
 * Main layout wrapper with sidebar and content area
 */
import { alpha } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Sidebar from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell = ({ children }: AppShellProps) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <Box
        component="main"
        sx={(theme) => ({
          flexGrow: 1,
          backgroundColor: theme.vars
            ? `rgba(${theme.vars.palette.background.defaultChannel} / 1)`
            : alpha(theme.palette.background.default, 1),
          overflow: 'auto',
        })}
      >
        <Box
          sx={{
            width: '100%',
            px: 3,
            pb: 5,
            pt: 3,
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default AppShell;
