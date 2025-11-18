/**
 * Sidebar Navigation Component
 * Left navigation drawer with menu items
 */
import { styled } from '@mui/material/styles';
import MuiDrawer, { drawerClasses } from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Avatar from '@mui/material/Avatar';
import HomeIcon from '@mui/icons-material/Home';
import ListIcon from '@mui/icons-material/List';
import ReceiptIcon from '@mui/icons-material/Receipt';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import SettingsIcon from '@mui/icons-material/Settings';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../store';

const drawerWidth = 240;

const Drawer = styled(MuiDrawer)({
  width: drawerWidth,
  flexShrink: 0,
  boxSizing: 'border-box',
  [`& .${drawerClasses.paper}`]: {
    width: drawerWidth,
    boxSizing: 'border-box',
  },
});

interface MenuItem {
  text: string;
  icon: React.ReactElement;
  path: string;
}

const menuItems: MenuItem[] = [
  { text: 'Dashboard', icon: <HomeIcon />, path: '/' },
  { text: 'Holdings', icon: <ListIcon />, path: '/holdings' },
  { text: 'Transactions', icon: <ReceiptIcon />, path: '/transactions' },
  { text: 'Analytics', icon: <TrendingUpIcon />, path: '/analytics' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

export const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);

  return (
    <Drawer
      variant="permanent"
      sx={{
        display: { xs: 'none', md: 'block' },
        [`& .${drawerClasses.paper}`]: {
          backgroundColor: 'background.paper',
          backgroundImage: 'none',
        },
      }}
    >
      {/* Logo/Brand */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          p: 2,
          gap: 1,
        }}
      >
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: 1,
            background: 'linear-gradient(135deg, hsl(210, 98%, 48%) 0%, hsl(210, 100%, 35%) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 700,
            fontSize: '1.2rem',
          }}
        >
          P
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Portfolio
        </Typography>
      </Box>
      
      <Divider />
      
      {/* Navigation Menu */}
      <Box
        sx={{
          overflow: 'auto',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <List sx={{ px: 2, py: 1 }}>
          {menuItems.map((item) => (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'action.selected',
                    '&:hover': {
                      backgroundColor: 'action.selected',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 36,
                    color: location.pathname === item.path ? 'primary.main' : 'text.secondary',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: location.pathname === item.path ? 600 : 400,
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
      
      {/* User Profile Section */}
      <Stack
        direction="row"
        sx={{
          p: 2,
          gap: 1,
          alignItems: 'center',
          borderTop: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Avatar
          sx={{
            width: 36,
            height: 36,
            bgcolor: 'primary.main',
          }}
        >
          {user?.email?.[0]?.toUpperCase() || 'U'}
        </Avatar>
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 500,
              lineHeight: '16px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {user?.first_name || 'User'}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              display: 'block',
            }}
          >
            {user?.email || 'user@email.com'}
          </Typography>
        </Box>
      </Stack>
    </Drawer>
  );
};

export default Sidebar;
