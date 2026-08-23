import { createContext, useCallback, useContext, useEffect, useState } from "react";

const AuthContext = createContext(null);

const TOKENS_KEY = "documind_auth_tokens";
const USER_KEY = "documind_auth_user";

const loadFromStorage = (key) => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  const [tokens, setTokens] = useState(() => loadFromStorage(TOKENS_KEY));
  const [user, setUser] = useState(() => loadFromStorage(USER_KEY));

  useEffect(() => {
    if (tokens) {
      localStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
    } else {
      localStorage.removeItem(TOKENS_KEY);
    }
  }, [tokens]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }, [user]);

  const login = useCallback((nextUser, nextTokens) => {
    setUser(nextUser);
    setTokens(nextTokens);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setTokens(null);
  }, []);

  const value = {
    user,
    tokens,
    isAuthenticated: Boolean(tokens?.access),
    login,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
};