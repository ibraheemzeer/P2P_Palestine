import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthState } from '../types';

interface AuthStore extends AuthState {
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isAdmin: false,

      setUser: (user) => {
        set({ 
          user, 
          isAuthenticated: !!user,
          isAdmin: user?.role === 'ADMIN' 
        });
        if (user) {
          localStorage.setItem('user', JSON.stringify(user));
        }
      },

      setToken: (token) => {
        set({ token });
        if (token) {
          localStorage.setItem('token', token);
        }
      },

      login: (user, token) => {
        set({ 
          user, 
          token, 
          isAuthenticated: true,
          isAdmin: user.role === 'ADMIN'
        });
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
      },

      logout: () => {
        set({ 
          user: null, 
          token: null, 
          isAuthenticated: false,
          isAdmin: false
        });
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
