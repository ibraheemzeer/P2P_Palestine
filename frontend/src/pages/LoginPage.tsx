import React from 'react';
import { useAuthStore } from '@store/authStore';
import { useLogin } from '@hooks/useQueries';
import { TextField, Button, Box, Typography, Container, Paper, Alert } from '@mui/material';
import { Link, useNavigate } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const loginMutation = useLogin();
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await loginMutation.mutateAsync({ username, password });
      if (response.data?.access_token) {
        login(response.data, response.data.access_token);
        navigate('/dashboard');
      }
    } catch (error: any) {
      console.error('Login failed:', error.response?.data || error.message);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography component="h1" variant="h5" align="center" gutterBottom>
            Sign In to P2P Palestine
          </Typography>

          {loginMutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {loginMutation.error instanceof Error ? loginMutation.error.message : 'Invalid credentials'}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username or Email"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? 'Signing in...' : 'Sign In'}
            </Button>
            <Typography align="center">
              Don't have an account?{' '}
              <Link to="/register" style={{ textDecoration: 'none' }}>
                Sign Up
              </Link>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};
