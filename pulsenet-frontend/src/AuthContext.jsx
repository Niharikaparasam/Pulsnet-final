// src/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, fetchCurrentUser } from "./api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setInitialLoading(false);
      return;
    }

    fetchCurrentUser()
      .then((u) => setUser(u))
      .catch(() => {
        localStorage.removeItem("access_token");
      })
      .finally(() => setInitialLoading(false));
  }, []);

  const login = async (email, password) => {
    const tokenData = await apiLogin(email, password);
    localStorage.setItem("access_token", tokenData.access_token);
    const me = await fetchCurrentUser();
    setUser(me);
    return me;
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  const value = { user, login, logout, initialLoading };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
