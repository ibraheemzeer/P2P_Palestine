import React from 'react';
import { useExchangeRates, useUpdateExchangeRate, useAllUsers, useApproveOrder, useRejectOrder } from '@hooks/useQueries';
import { 
  Box, 
  Typography, 
  Container, 
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Tabs,
  Tab,
  CircularProgress
} from '@mui/material';

export const AdminPage: React.FC = () => {
  const [tabValue, setTabValue] = React.useState(0);
  const { data: exchangeRates, isLoading: ratesLoading } = useExchangeRates();
  const { data: users, isLoading: usersLoading } = useAllUsers();
  const updateRateMutation = useUpdateExchangeRate();
  const approveMutation = useApproveOrder();
  const rejectMutation = useRejectOrder();
  
  const [rateDialogOpen, setRateDialogOpen] = React.useState(false);
  const [newRate, setNewRate] = React.useState({ pair: '', rate: '' });

  const handleUpdateRate = async () => {
    try {
      await updateRateMutation.mutateAsync({
        currencyPair: newRate.pair,
        rate: parseFloat(newRate.rate),
      });
      setRateDialogOpen(false);
      setNewRate({ pair: '', rate: '' });
    } catch (error) {
      console.error('Failed to update rate:', error);
    }
  };

  if (ratesLoading || usersLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Exchange Rates" />
          <Tab label="Users Management" />
          <Tab label="Orders Review" />
        </Tabs>
      </Box>

      {/* Exchange Rates Tab */}
      {tabValue === 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Current Exchange Rates</Typography>
            <Button variant="contained" onClick={() => setRateDialogOpen(true)}>
              Update Rate
            </Button>
          </Box>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Currency Pair</TableCell>
                  <TableCell>Rate</TableCell>
                  <TableCell>Last Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {exchangeRates?.map((rate) => (
                  <TableRow key={rate.id}>
                    <TableCell>{rate.currency_pair}</TableCell>
                    <TableCell>{rate.rate}</TableCell>
                    <TableCell>{new Date(rate.created_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Users Tab */}
      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>All Users</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Display Name</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Joined</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users?.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.id}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.public_display_name}</TableCell>
                    <TableCell>
                      <Chip 
                        label={user.role} 
                        color={user.role === 'ADMIN' ? 'error' : 'primary'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={user.is_active ? 'Active' : 'Inactive'} 
                        color={user.is_active ? 'success' : 'default'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Orders Review Tab */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Pending Orders for Review</Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Review and approve/reject pending orders with proof of funds
          </Typography>
          <Alert severity="info">
            This section will display pending orders requiring admin approval.
            Use the order management endpoints to approve or reject with reasons.
          </Alert>
        </Paper>
      )}

      {/* Update Rate Dialog */}
      <Dialog open={rateDialogOpen} onClose={() => setRateDialogOpen(false)}>
        <DialogTitle>Update Exchange Rate</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1, minWidth: 300 }}>
            <TextField
              select
              label="Currency Pair"
              value={newRate.pair}
              onChange={(e) => setNewRate({ ...newRate, pair: e.target.value })}
              SelectProps={{ native: true }}
              fullWidth
            >
              <option value="">Select pair</option>
              <option value="USD/ILS">USD/ILS</option>
              <option value="USD/JOD">USD/JOD</option>
              <option value="ILS/USD">ILS/USD</option>
              <option value="JOD/USD">JOD/USD</option>
            </TextField>
            <TextField
              label="New Rate"
              type="number"
              value={newRate.rate}
              onChange={(e) => setNewRate({ ...newRate, rate: e.target.value })}
              fullWidth
              inputProps={{ step: 0.0001 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleUpdateRate} 
            variant="contained"
            disabled={updateRateMutation.isPending || !newRate.pair || !newRate.rate}
          >
            {updateRateMutation.isPending ? 'Updating...' : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

// Simple Alert component since we didn't import it
const Alert = ({ severity, children }: { severity: string; children: React.ReactNode }) => (
  <Box sx={{ 
    p: 2, 
    mb: 2, 
    borderRadius: 1,
    backgroundColor: severity === 'info' ? '#e3f2fd' : '#fff3cd',
    borderLeft: `4px solid ${severity === 'info' ? '#2196f3' : '#ffc107'}`
  }}>
    {children}
  </Box>
);
