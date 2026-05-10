import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orderService, transactionService, adminService, authService } from '../services';

// Auth Queries
export const useLogin = () => {
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authService.login(username, password),
  });
};

export const useRegister = () => {
  return useMutation({
    mutationFn: ({ username, email, password, full_name }: { username: string; email: string; password: string; full_name?: string }) =>
      authService.register(username, email, password, full_name),
  });
};

export const useCurrentUser = () => {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: authService.getCurrentUser,
    retry: false,
  });
};

// Order Queries
export const useOrders = () => {
  return useQuery({
    queryKey: ['orders'],
    queryFn: orderService.getAllOrders,
  });
};

export const useOrder = (orderId: number) => {
  return useQuery({
    queryKey: ['order', orderId],
    queryFn: () => orderService.getOrderById(orderId),
    enabled: !!orderId,
  });
};

export const useCreateOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: orderService.createOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};

export const useDeleteOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: orderService.deleteOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};

// Transaction Queries
export const useTransactions = () => {
  return useQuery({
    queryKey: ['transactions'],
    queryFn: transactionService.getAllTransactions,
  });
};

export const useMatchTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: transactionService.matchTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};

export const useLockEscrow = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: transactionService.lockEscrow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
};

export const useReleaseFunds = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: transactionService.releaseFunds,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
};

export const useDisputeTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: transactionService.disputeTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
};

// Admin Queries
export const useExchangeRates = () => {
  return useQuery({
    queryKey: ['exchangeRates'],
    queryFn: adminService.getExchangeRates,
  });
};

export const useUpdateExchangeRate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminService.updateExchangeRate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exchangeRates'] });
    },
  });
};

export const useAllUsers = () => {
  return useQuery({
    queryKey: ['allUsers'],
    queryFn: adminService.getAllUsers,
  });
};

export const useApproveOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminService.approveOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};

export const useRejectOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adminService.rejectOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: adminService.getDashboardStats,
    enabled: true,
  });
};
