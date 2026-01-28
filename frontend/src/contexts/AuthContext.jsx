import React, { useState, createContext, useContext, useEffect } from "react";
import { authAPI } from "../lib/api";

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

// Role definitions for display
export const ROLE_DEFINITIONS = {
  admin: {
    label: "Administrator",
    description: "Full access to all features",
    color: "text-purple-400",
    bgColor: "bg-purple-500/20",
  },
  analyst: {
    label: "Fraud Analyst",
    description: "War Room, Brain Surgery, Metrics, Evidence",
    color: "text-blue-400",
    bgColor: "bg-blue-500/20",
  },
  engineer: {
    label: "Security Engineer",
    description: "Rules, RSB Manager, Diff Viewer",
    color: "text-green-400",
    bgColor: "bg-green-500/20",
  },
  compliance: {
    label: "Compliance Officer",
    description: "Approvals, Evidence, Metrics",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/20",
  },
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDemoUser, setIsDemoUser] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem("ff_token");
    const savedDemoRole = localStorage.getItem("ff_demo_role");
    
    if (token) {
      try {
        const response = await authAPI.getMe();
        const userData = response.data;
        
        // Check if this is a demo user
        if (userData.email === "demo@fraudforge.io") {
          setIsDemoUser(true);
          // Apply saved demo role if exists
          if (savedDemoRole) {
            userData.role = savedDemoRole;
          } else {
            userData.role = "admin"; // Default demo role is admin (full access)
          }
        }
        
        setUser(userData);
      } catch (error) {
        localStorage.removeItem("ff_token");
        localStorage.removeItem("ff_demo_role");
        setUser(null);
        setIsDemoUser(false);
      }
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    const response = await authAPI.login({ email, password });
    localStorage.setItem("ff_token", response.data.token);
    
    const userData = response.data.user;
    if (userData.email === "demo@fraudforge.io") {
      setIsDemoUser(true);
      userData.role = "admin"; // Demo users start as admin
      localStorage.setItem("ff_demo_role", "admin");
    }
    
    setUser(userData);
    return response.data;
  };

  const register = async (email, password, name, role = "analyst") => {
    const response = await authAPI.register({ email, password, name, role });
    localStorage.setItem("ff_token", response.data.token);
    
    const userData = response.data.user;
    if (userData.email === "demo@fraudforge.io") {
      setIsDemoUser(true);
      userData.role = "admin";
      localStorage.setItem("ff_demo_role", "admin");
    }
    
    setUser(userData);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem("ff_token");
    localStorage.removeItem("ff_demo_role");
    setUser(null);
    setIsDemoUser(false);
  };

  // Switch role for demo user
  const switchRole = (newRole) => {
    if (!isDemoUser) return;
    
    setUser(prev => ({
      ...prev,
      role: newRole,
    }));
    localStorage.setItem("ff_demo_role", newRole);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      login, 
      register, 
      logout, 
      isAuthenticated: !!user,
      isDemoUser,
      switchRole,
      roleDefinitions: ROLE_DEFINITIONS,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;
