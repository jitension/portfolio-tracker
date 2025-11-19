/**
 * Link Robinhood Account Dialog
 * Modal dialog for linking a new Robinhood account with 2FA support
 */
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import { useAppDispatch, useAppSelector } from '../../../store';
import { linkAccount, clearMfaRequired } from '../store/robinhoodSlice';

interface LinkRobinhoodDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const steps = ['Enter Credentials', '2FA Verification', 'Success'];

export const LinkRobinhoodDialog: React.FC<LinkRobinhoodDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const dispatch = useAppDispatch();
  const { isLinking, linkingError, mfaRequired, mfaType } = useAppSelector(
    (state) => state.robinhood
  );

  const [activeStep, setActiveStep] = useState(0);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');

  // Reset form when dialog closes
  useEffect(() => {
    if (!open) {
      setActiveStep(0);
      setUsername('');
      setPassword('');
      setMfaCode('');
      dispatch(clearMfaRequired());
    }
  }, [open, dispatch]);

  // Handle MFA required response
  useEffect(() => {
    if (mfaRequired && activeStep === 0) {
      setActiveStep(1);
    }
  }, [mfaRequired, activeStep]);

  const handleSubmit = async () => {
    if (activeStep === 0) {
      // Step 1: Submit credentials
      const result = await dispatch(
        linkAccount({
          username,
          password,
        })
      );

      if (linkAccount.fulfilled.match(result)) {
        // Success - either direct or after push approval
        setActiveStep(2);
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 1500);
      }
      // If MFA required, the useEffect will handle moving to step 1
      // Note: Backend handles push notification and waits up to 120s
    } else if (activeStep === 1) {
      // Step 2: Submit MFA code
      const result = await dispatch(
        linkAccount({
          username,
          password,
          mfa_code: mfaCode,
        })
      );

      if (linkAccount.fulfilled.match(result)) {
        setActiveStep(2);
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 1500);
      }
    }
  };

  const handleClose = () => {
    if (!isLinking) {
      onClose();
    }
  };

  const isStep0Valid = username && password;
  const isStep1Valid = mfaCode && mfaCode.length === 6;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Link Robinhood Account</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 3, mt: 1 }}>
          <Stepper activeStep={activeStep}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        {linkingError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {linkingError}
          </Alert>
        )}

        {activeStep === 0 && (
          <Box>
            {!isLinking && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Enter your Robinhood credentials. Your password is encrypted and stored securely.
              </Typography>
            )}
            
            {isLinking && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  📱 Check your Robinhood app!
                </Typography>
                <Typography variant="body2">
                  A push notification may be sent to your phone. Please approve the login request if prompted.
                  Waiting up to 2 minutes for approval...
                </Typography>
              </Alert>
            )}
            
            <TextField
              autoFocus
              margin="dense"
              label="Robinhood Email"
              type="email"
              fullWidth
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLinking}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Robinhood Password"
              type="password"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLinking}
            />
            
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Note: You may receive a push notification in your Robinhood app to approve the login.
            </Typography>
          </Box>
        )}

        {activeStep === 1 && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Enter the 6-digit verification code from your authenticator app or SMS.
            </Typography>
            <TextField
              autoFocus
              margin="dense"
              label="6-Digit Code"
              type="text"
              fullWidth
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              disabled={isLinking}
              inputProps={{ maxLength: 6 }}
              helperText="Enter the 6-digit verification code"
            />
          </Box>
        )}

        {activeStep === 2 && (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="h6" color="success.main" gutterBottom>
              ✓ Account Linked Successfully!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your Robinhood account has been connected.
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        {activeStep < 2 && (
          <>
            <Button onClick={handleClose} disabled={isLinking}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              variant="contained"
              disabled={
                isLinking ||
                (activeStep === 0 && !isStep0Valid) ||
                (activeStep === 1 && !isStep1Valid)
              }
              startIcon={isLinking ? <CircularProgress size={20} /> : null}
            >
              {isLinking ? 'Connecting...' : activeStep === 0 ? 'Continue' : 'Link Account'}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default LinkRobinhoodDialog;
