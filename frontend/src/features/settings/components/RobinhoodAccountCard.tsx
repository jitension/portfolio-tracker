/**
 * Robinhood Account Card Component
 * Displays a linked Robinhood account with actions
 */
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Sync as SyncIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import type { RobinhoodAccount } from '../types';

interface RobinhoodAccountCardProps {
  account: RobinhoodAccount;
  onTestConnection: (accountId: string) => void;
  onUnlink: (accountId: string) => void;
  isLoading?: boolean;
}

export const RobinhoodAccountCard: React.FC<RobinhoodAccountCardProps> = ({
  account,
  onTestConnection,
  onUnlink,
  isLoading = false,
}) => {
  const [unlinkDialogOpen, setUnlinkDialogOpen] = useState(false);

  const getStatusColor = () => {
    switch (account.sync_status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = () => {
    switch (account.sync_status) {
      case 'success':
        return <CheckCircleIcon fontSize="small" />;
      case 'failed':
        return <ErrorIcon fontSize="small" />;
      default:
        return null;
    }
  };

  const getStatusLabel = () => {
    switch (account.sync_status) {
      case 'success':
        return 'Connected';
      case 'failed':
        return 'Connection Failed';
      case 'pending':
        return 'Syncing';
      case 'never_synced':
        return 'Not Synced';
      default:
        return 'Unknown';
    }
  };

  const formatLastSync = () => {
    if (!account.last_sync) return 'Never';
    const date = new Date(account.last_sync);
    return date.toLocaleString();
  };

  const handleUnlink = () => {
    onUnlink(account.id);
    setUnlinkDialogOpen(false);
  };

  return (
    <>
      <Card variant="outlined">
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Account {account.account_number}
              </Typography>
              <Chip
                label={account.account_type.toUpperCase()}
                size="small"
                color="primary"
                sx={{ mr: 1 }}
              />
              <Chip
                icon={getStatusIcon() || undefined}
                label={getStatusLabel()}
                size="small"
                color={getStatusColor()}
              />
            </Box>
            <IconButton
              size="small"
              color="error"
              onClick={() => setUnlinkDialogOpen(true)}
              disabled={isLoading}
            >
              <DeleteIcon />
            </IconButton>
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              2FA: {account.mfa_enabled ? `Enabled (${account.mfa_type.toUpperCase()})` : 'Disabled'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Last Sync: {formatLastSync()}
            </Typography>
            {account.sync_error && (
              <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                Error: {account.sync_error}
              </Typography>
            )}
          </Box>
        </CardContent>

        <CardActions>
          <Button
            size="small"
            startIcon={<SyncIcon />}
            onClick={() => onTestConnection(account.id)}
            disabled={isLoading}
          >
            Test Connection
          </Button>
        </CardActions>
      </Card>

      {/* Unlink Confirmation Dialog */}
      <Dialog open={unlinkDialogOpen} onClose={() => setUnlinkDialogOpen(false)}>
        <DialogTitle>Unlink Robinhood Account?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to unlink account {account.account_number}? This will stop syncing
            data from Robinhood. You can re-link the account later if needed.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUnlinkDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUnlink} color="error" variant="contained">
            Unlink
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default RobinhoodAccountCard;
