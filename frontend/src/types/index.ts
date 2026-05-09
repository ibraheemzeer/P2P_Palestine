export interface User {
  id: number;
  email: string;
  role: 'USER' | 'ADMIN';
  public_display_name: string;
  bank_details?: Record<string, any>;
  crypto_addresses?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Order {
  id: number;
  user_id: number;
  type: 'BUY' | 'SELL';
  currency: 'USD' | 'ILS' | 'JOD';
  blockchain_network: 'TRX' | 'BNB' | 'SOL' | 'ETH';
  min_amount: number;
  max_amount: number;
  commission: number;
  status: 'PENDING' | 'ACTIVE' | 'REJECTED';
  proof_of_funds_url?: string;
  creator_display_name?: string;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: number;
  order_id: number;
  buyer_id: number;
  seller_id: number;
  base_amount: number;
  exchange_rate: number;
  currency: string;
  buyer_pays: number;
  seller_receives: number;
  platform_fee: number;
  status: 'MATCHED' | 'ESCROW_LOCKED' | 'COMPLETED' | 'DISPUTED';
  escrow_locked_at?: string;
  completed_at?: string;
  disputed_at?: string;
  created_at: string;
}

export interface ExchangeRate {
  id: number;
  currency_pair: string;
  rate: number;
  updated_by: number;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  detail?: string;
}
