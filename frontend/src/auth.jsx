/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState } from 'react';
import api from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api.get('/auth/me')
      .then(({ data }) => { if (!cancelled) setUser(data); })
      .catch(() => { if (!cancelled) setUser(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password});
    setUser(data);
  };

  const register = async (username, email, password) => {
    await api.post('/auth/register', { username, email, password});
  };

  const logout = async () => {
    await api.post('/auth/logout');
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
