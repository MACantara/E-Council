import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { getMe, login as loginApi, logout as logoutApi, register as registerApi } from '@/api/auth';
import type { User, LoginCredentials, RegisterData } from '@/api/auth';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const restoreSession = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const currentUser = await getMe();
      setUser(currentUser);
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    restoreSession();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const tokens = await loginApi(credentials);
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    const currentUser = await getMe();
    setUser(currentUser);
  };

  const register = async (data: RegisterData) => {
    await registerApi(data);
  };

  const logout = async () => {
    try {
      await logoutApi();
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    }
  };

  const refetchUser = async () => {
    const currentUser = await getMe();
    setUser(currentUser);
  };

  const isAuthenticated = user !== null;
  const isAdmin = user?.users_role === 'Admin';

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        isAdmin,
        login,
        register,
        logout,
        refetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
