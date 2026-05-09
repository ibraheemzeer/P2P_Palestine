import React from 'react';
import { useOrders, useCreateOrder, useDeleteOrder } from '@hooks/useQueries';
import { 
  Box, 
  Typography, 
  Container, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert
} from '@mui/material';
import { Order } from '@types/index';

export const OrdersPage: React.FC = () => {
  const { data: orders, isLoading } = useOrders();
  const createMutation = useCreateOrder();
  const deleteMutation = useDeleteOrder();
  const [openDialog, setOpenDialog] = React.useState(false);
  const [formData, setFormData] = React.useState({
    type: 'BUY' as 'BUY' | 'SELL',
    currency: 'USD' as 'USD' | 'ILS' | 'JOD',
    blockchain_network: 'TRX' as 'TRX' | 'BNB' | 'SOL' | 'ETH',
    min_amount: '',
    max_amount: '',
    commission: '',
  });

  const handleCreate = async () => {
    try {
      await createMutation.mutateAsync({
        ...formData,
        min_amount: parseFloat(formData.min_amount),
        max_amount: parseFloat(formData.max_amount),
        commission: parseFloat(formData.commission),
      });
      setOpenDialog(false);
      setFormData({
        type: 'BUY',
        currency: 'USD',
        blockchain_network: 'TRX',
        min_amount: '',
        max_amount: '',
        commission: '',
      });
    } catch (error) {
      console.error('Failed to create order:', error);
    }
  };

  const handleDelete = async (orderId: number) => {
    if (window.confirm('Are you sure you want to cancel this order?')) {
      try {
        await deleteMutation.mutateAsync(orderId);
      } catch (error) {
        console.error('Failed to delete order:', error);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING': return 'warning';
      case 'ACTIVE': return 'success';
      case 'REJECTED': return 'error';
      default: return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Orders</Typography>
        <Button variant="contained" onClick={() => setOpenDialog(true)}>
          Create New Order
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Currency</TableCell>
              <TableCell>Network</TableCell>
              <TableCell>Min Amount</TableCell>
              <TableCell>Max Amount</TableCell>
              <TableCell>Commission</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Creator</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders?.map((order: Order) => (
              <TableRow key={order.id}>
                <TableCell>{order.id}</TableCell>
                <TableCell>
                  <Chip label={order.type} color={order.type === 'BUY' ? 'success' : 'error'} size="small" />
                </TableCell>
                <TableCell>{order.currency}</TableCell>
                <TableCell>{order.blockchain_network}</TableCell>
                <TableCell>{order.min_amount}</TableCell>
                <TableCell>{order.max_amount}</TableCell>
                <TableCell>{(order.commission * 100).toFixed(2)}%</TableCell>
                <TableCell>
                  <Chip label={order.status} color={getStatusColor(order.status)} size="small" />
                </TableCell>
                <TableCell>{order.creator_display_name || `User_${order.user_id}`}</TableCell>
                <TableCell>
                  <Button 
                    size="small" 
                    color="error"
                    onClick={() => handleDelete(order.id)}
                    disabled={order.status !== 'PENDING' && order.status !== 'ACTIVE'}
                  >
                    Cancel
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Order Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Order</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              select
              label="Order Type"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as 'BUY' | 'SELL' })}
              SelectProps={{ native: true }}
              fullWidth
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </TextField>

            <TextField
              select
              label="Currency"
              value={formData.currency}
              onChange={(e) => setFormData({ ...formData, currency: e.target.value as 'USD' | 'ILS' | 'JOD' })}
              SelectProps={{ native: true }}
              fullWidth
            >
              <option value="USD">USD</option>
              <option value="ILS">ILS</option>
              <option value="JOD">JOD</option>
            </TextField>

            <TextField
              select
              label="Blockchain Network"
              value={formData.blockchain_network}
              onChange={(e) => setFormData({ ...formData, blockchain_network: e.target.value as 'TRX' | 'BNB' | 'SOL' | 'ETH' })}
              SelectProps={{ native: true }}
              fullWidth
            >
              <option value="TRX">TRX (Tron)</option>
              <option value="BNB">BNB (Binance)</option>
              <option value="SOL">SOL (Solana)</option>
              <option value="ETH">ETH (Ethereum)</option>
            </TextField>

            <TextField
              label="Minimum Amount"
              type="number"
              value={formData.min_amount}
              onChange={(e) => setFormData({ ...formData, min_amount: e.target.value })}
              fullWidth
            />

            <TextField
              label="Maximum Amount"
              type="number"
              value={formData.max_amount}
              onChange={(e) => setFormData({ ...formData, max_amount: e.target.value })}
              fullWidth
            />

            <TextField
              label="Commission (%)"
              type="number"
              value={formData.commission}
              onChange={(e) => setFormData({ ...formData, commission: e.target.value })}
              helperText="Seller commission (0-3.5%)"
              inputProps={{ step: 0.01, min: 0, max: 0.035 }}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreate} 
            variant="contained"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create Order'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
