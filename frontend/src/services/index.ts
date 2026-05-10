import api from './api';
import { User, Order, Transaction, ExchangeRate, ApiResponse } from '../types';

export const authService = {
  login: async (username: string, password: string) => {
    const response = await api.post<ApiResponse<{ access_token: string }>>('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  register: async (username: string, email: string, password: string, full_name?: string) => {
    const response = await api.post<ApiResponse<User>>('/auth/register', {
      username,
      email,
      password,
      full_name,
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get<User>('/users/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

export const orderService = {
  getAllOrders: async () => {
    const response = await api.get<Order[]>('/orders/');
    return response.data;
  },

  getOrderById: async (orderId: number) => {
    const response = await api.get<Order>(`/orders/${orderId}`);
    return response.data;
  },

  createOrder: async (orderData: Partial<Order>, proofFile?: File) => {
    const formData = new FormData();
    formData.append('type', orderData.type!);
    formData.append('currency', orderData.currency!);
    formData.append('blockchain_network', orderData.blockchain_network!);
    formData.append('min_amount', orderData.min_amount!.toString());
    formData.append('max_amount', orderData.max_amount!.toString());
    formData.append('commission', orderData.commission!.toString());

    if (proofFile) {
      formData.append('proof_of_funds', proofFile);
    }

    const response = await api.post<Order>('/orders/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  updateOrder: async (orderId: number, orderData: Partial<Order>) => {
    const response = await api.put<Order>(`/orders/${orderId}`, orderData);
    return response.data;
  },

  deleteOrder: async (orderId: number) => {
    const response = await api.delete(`/orders/${orderId}`);
    return response.data;
  },
};

export const transactionService = {
  getAllTransactions: async () => {
    const response = await api.get<Transaction[]>('/transactions/');
    return response.data;
  },

  getTransactionById: async (transactionId: number) => {
    const response = await api.get<Transaction>(`/transactions/${transactionId}`);
    return response.data;
  },

  matchTransaction: async (orderId: number) => {
    const response = await api.post<Transaction>(`/transactions/${orderId}/match`);
    return response.data;
  },

  lockEscrow: async (transactionId: number) => {
    const response = await api.post<Transaction>(`/transactions/${transactionId}/lock-escrow`);
    return response.data;
  },

  releaseFunds: async (transactionId: number) => {
    const response = await api.post<Transaction>(`/transactions/${transactionId}/release`);
    return response.data;
  },

  disputeTransaction: async (transactionId: number) => {
    const response = await api.post<Transaction>(`/transactions/${transactionId}/dispute`);
    return response.data;
  },
};

export const adminService = {
  getExchangeRates: async () => {
    const response = await api.get<ExchangeRate[]>('/admin/exchange-rates');
    return response.data;
  },

  updateExchangeRate: async (currencyPair: string, rate: number) => {
    const response = await api.post<ExchangeRate>('/admin/exchange-rates', {
      currency_pair: currencyPair,
      rate,
    });
    return response.data;
  },

  getAllUsers: async () => {
    const response = await api.get<User[]>('/admin/users');
    return response.data;
  },

  approveOrder: async (orderId: number) => {
    const response = await api.put<Order>(`/admin/orders/${orderId}/approve`);
    return response.data;
  },

  rejectOrder: async (orderId: number, reason: string) => {
    const response = await api.put<Order>(`/admin/orders/${orderId}/reject`, { reason });
    return response.data;
  },

  resolveDispute: async (transactionId: number, decision: 'BUYER' | 'SELLER') => {
    const response = await api.post<Transaction>(`/admin/transactions/${transactionId}/resolve-dispute`, {
      decision,
    });
    return response.data;
  },

  getDashboardStats: async () => {
    const response = await api.get<{
      total_users: number;
      total_orders: number;
      total_transactions: number;
      total_volume: number;
      pending_orders: number;
      active_transactions: number;
    }>('/admin/stats');
    return response.data;
  },
};
