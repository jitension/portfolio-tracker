/**
 * Settings Page Component
 * Main settings page with Robinhood account management
 */
import { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Snackbar,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../../store';
import {
  fetchAccounts,
  unlinkAccount,
  testAccountConnection,
  clearError,
} from '../store/robinhoodSlice';
import LinkRobinhoodDialog from './LinkRobinhoodDialog';
import RobinhoodAccountCard from './RobinhoodAccountCard';

export const SettingsPage = () => {
  const dispatch = useAppDispatch();
  const { accounts, isLoading, error } = useAppSelector((state) => state.robinhood);
  
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    dispatch(fetchAccounts());
  }, [dispatch]);

  const handleLinkSuccess = () => {
    setSuccessMessage('Robinhood account linked successfully!');
    dispatch(fetchAccounts());
  };

  const handleTestConnection = (accountId: string) => {
    dispatch(testAccountConnection({ accountId }));
  };

  const handleUnlink = async (accountId: string) => {
    await dispatch(unlinkAccount(accountId));
    setSuccessMessage('Account unlinked successfully');
  };

  const handleCloseSnackbar = () => {
    setSuccessMessage('');
  };

  const handleCloseError = () => {
    dispatch(clearError());
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your Robinhood account connections and preferences
        </Typography>
      </Box>

      {/* Robinhood Accounts Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Robinhood Accounts
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Link your Robinhood account to sync portfolio data automatically
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setLinkDialogOpen(true)}
          >
            Link Account
          </Button>
        </Box>

        {error && (
          <Alert severity="error" onClose={handleCloseError} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {isLoading && accounts.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : accounts.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              No Robinhood accounts linked yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Link your account to start syncing your portfolio data
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {accounts.map((account) => (
              <Grid key={account.id} size={{ xs: 12, md: 6 }}>
                <RobinhoodAccountCard
                  account={account}
                  onTestConnection={handleTestConnection}
                  onUnlink={handleUnlink}
                  isLoading={isLoading}
                />
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* Link Account Dialog */}
      <LinkRobinhoodDialog
        open={linkDialogOpen}
        onClose={() => setLinkDialogOpen(false)}
        onSuccess={handleLinkSuccess}
      />

      {/* Success Snackbar */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          {successMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default SettingsPage;
