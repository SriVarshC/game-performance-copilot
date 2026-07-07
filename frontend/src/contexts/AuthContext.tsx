import { createContext, useContext, useState, type ReactNode } from "react";
import { postLogin, postRegister } from "../services/api";
import type { LoginRequest, RegisterRequest } from "../types";

interface AuthContextType {
  username: string | null;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(
    localStorage.getItem("gc_username")
  );

  const login = async (data: LoginRequest) => {
    const res = await postLogin(data);
    localStorage.setItem("gc_token", res.access_token);
    localStorage.setItem("gc_username", res.username);
    setUsername(res.username);
  };

  const register = async (data: RegisterRequest) => {
    const res = await postRegister(data);
    localStorage.setItem("gc_token", res.access_token);
    localStorage.setItem("gc_username", res.username);
    setUsername(res.username);
  };

  const logout = () => {
    localStorage.removeItem("gc_token");
    localStorage.removeItem("gc_username");
    setUsername(null);
  };

  return (
    <AuthContext.Provider
      value={{ username, isAuthenticated: !!username, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}