import React from 'react';
import { useTransactions, useMatchTransaction, useLockEscrow, useReleaseFunds, useDisputeTransaction } from '@hooks/useQueries';
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
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import { Transaction } from '@types/index';
import { Lock, Unlock, CheckCircle, ReportProblem } from '@mui/icons-material';

export const TransactionsPage: React.FC = () => {
  const { data: transactions, isLoading } = useTransactions();
  const matchMutation = useMatchTransaction();
  const lockMutation = useLockEscrow();
  const releaseMutation = useReleaseFunds();
  const disputeMutation = useDisputeTransaction();

  const handleMatch = async (orderId: number) => {
    try {
      await matchMutation.mutateAsync(orderId);
    } catch (error) {
      console.error('Failed to match transaction:', error);
    }
  };

  const handleLockEscrow = async (transactionId: number) => {
    try {
      await lockMutation.mutateAsync(transactionId);
    } catch (error) {
      console.error('Failed to lock escrow:', error);
    }
  };

  const handleRelease = async (transactionId: number) => {
    if (window.confirm('Confirm fund release?')) {
      try {
        await releaseMutation.mutateAsync(transactionId);
      } catch (error) {
        console.error('Failed to release funds:', error);
      }
    }
  };

  const handleDispute = async (transactionId: number) => {
    if (window.confirm('Open dispute for this transaction?')) {
      try {
        await disputeMutation.mutateAsync(transactionId);
      } catch (error) {
        console.error('Failed to dispute transaction:', error);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'MATCHED': return 'info';
      case 'ESCROW_LOCKED': return 'warning';
      case 'COMPLETED': return 'success';
      case 'DISPUTED': return 'error';
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
      <Typography variant="h4" gutterBottom>
        Transactions
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Order ID</TableCell>
              <TableCell>Base Amount</TableCell>
              <TableCell>Exchange Rate</TableCell>
              <TableCell>Currency</TableCell>
              <TableCell>Buyer Pays</TableCell>
              <TableCell>Seller Receives</TableCell>
              <TableCell>Platform Fee</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {transactions?.map((tx: Transaction) => (
              <TableRow key={tx.id}>
                <TableCell>{tx.id}</TableCell>
                <TableCell>{tx.order_id}</TableCell>
                <TableCell>{tx.base_amount}</TableCell>
                <TableCell>{tx.exchange_rate}</TableCell>
                <TableCell>{tx.currency}</TableCell>
                <TableCell>{tx.buyer_pays.toFixed(2)}</TableCell>
                <TableCell>{tx.seller_receives.toFixed(2)}</TableCell>
                <TableCell>{tx.platform_fee.toFixed(2)}</TableCell>
                <TableCell>
                  <Chip label={tx.status} color={getStatusColor(tx.status)} size="small" />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {tx.status === 'MATCHED' && (
                      <Tooltip title="Lock Escrow">
                        <IconButton 
                          size="small" 
                          color="warning"
                          onClick={() => handleLockEscrow(tx.id)}
                          disabled={lockMutation.isPending}
                        >
                          <Lock />
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    {tx.status === 'ESCROW_LOCKED' && (
                      <>
                        <Tooltip title="Release Funds">
                          <IconButton 
                            size="small" 
                            color="success"
                            onClick={() => handleRelease(tx.id)}
                            disabled={releaseMutation.isPending}
                          >
                            <Unlock />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Report Dispute">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDispute(tx.id)}
                            disabled={disputeMutation.isPending}
                          >
                            <ReportProblem />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};
