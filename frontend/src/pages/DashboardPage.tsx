import React from 'react';
import { useDashboardStats } from '@hooks/useQueries';
import { useAuthStore } from '@store/authStore';
import { 
  Box, 
  Typography, 
  Container, 
  Grid, 
  Paper, 
  CircularProgress,
  Card,
  CardContent
} from '@mui/material';
import { 
  People as PeopleIcon, 
  ShoppingCart as OrdersIcon, 
  SwapHoriz as TransactionsIcon,
  AccountBalance as VolumeIcon,
  PendingActions as PendingIcon,
  Lock as LockIcon
} from '@mui/icons-material';

export const DashboardPage: React.FC = () => {
  const { data: stats, isLoading, error } = useDashboardStats();
  const { user, isAdmin } = useAuthStore();

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container>
        <Typography color="error">Failed to load dashboard data</Typography>
      </Container>
    );
  }

  const statCards = [
    { title: 'Total Users', value: stats?.total_users || 0, icon: <PeopleIcon />, color: '#1976d2' },
    { title: 'Total Orders', value: stats?.total_orders || 0, icon: <OrdersIcon />, color: '#2e7d32' },
    { title: 'Total Transactions', value: stats?.total_transactions || 0, icon: <TransactionsIcon />, color: '#ed6c02' },
    { title: 'Total Volume (USDT)', value: stats?.total_volume?.toFixed(2) || '0.00', icon: <VolumeIcon />, color: '#9c27b0' },
    { title: 'Pending Orders', value: stats?.pending_orders || 0, icon: <PendingIcon />, color: '#f57c00' },
    { title: 'Active Escrows', value: stats?.active_transactions || 0, icon: <LockIcon />, color: '#d32f2f' },
  ];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome{user ? `, ${user.public_display_name}` : ''}!
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {isAdmin ? 'Admin Dashboard' : 'User Dashboard'} - P2P Palestine Trading Platform
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {statCards.map((stat) => (
          <Grid item xs={12} sm={6} md={4} key={stat.title}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" variant="subtitle2" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4">{stat.value}</Typography>
                  </Box>
                  <Box sx={{ 
                    backgroundColor: stat.color, 
                    borderRadius: '50%', 
                    p: 1.5,
                    color: 'white'
                  }}>
                    {stat.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {isAdmin && (
        <Paper sx={{ mt: 4, p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Typography variant="body2" color="text.secondary">
            As an admin, you can manage exchange rates, approve/reject orders, resolve disputes, and view all transactions.
            Navigate to the Admin panel for full control.
          </Typography>
        </Paper>
      )}
    </Container>
  );
};
