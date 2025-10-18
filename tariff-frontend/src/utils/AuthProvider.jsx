import { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import { getRoleFromToken } from './jwtDecoder';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userRole, setUserRole] = useState(null);

  // Restore user on initial load
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    const savedToken = localStorage.getItem("accessToken");
    
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    
    // Extract role from JWT token (single source of truth)
    if (savedToken) {
      const role = getRoleFromToken(savedToken);
      setUserRole(role);
    }
  }, []);

  // Update role when user changes
  useEffect(() => {
    const savedToken = localStorage.getItem("accessToken");
    
    if (user && savedToken) {
      const role = getRoleFromToken(savedToken);
      setUserRole(role);
    } else {
      setUserRole(null);
    }
  }, [user]);

  const value = {
    user,
    setUser,
    userRole,
    isAdmin: userRole === 'admin',
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
